from http.server import HTTPServer
import re
import os.path
import json
import urllib.request as request
import http.client as httplib
import logging
import schedule
import time
from .messagerouter import MessageRouter
from .messages_collector import MessagesCollector
import threading
import sqlite3


player_data_file = os.path.join('.', 'data', 'player_data.json')
config_file = os.path.join('.', 'data', 'config.json')

class ExtBot():
    def __init__(self, bot_id):
        self.logger = logging.getLogger('extlog')

        with open(config_file) as data_file:
            config = json.load(data_file)


        self.bot_id = config['bot_id']
        self.refresh_days = config['refresh_days']

        self.messages_collection = MessagesCollector()

        self._init_regexes()

        self.logger.info("Bot initialized; bot_id=%s", bot_id)

    #related to logging
    def _attach_debug_handler(self):
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    #regular expression for parsing recieved messages
    def _init_regexes(self):
        #regex building blocks

        self.likes = re.compile(r'^' + '!likes')
        self.likesrank = re.compile(r'^' + '!rank')
        self.randomimage = re.compile(r'^' + '!image')
        self.kicks = re.compile(r'^' + '!kicks')
        self.groupinfo = re.compile(r'^' + '!info')

        self.help_regex = re.compile(r'^!help *')

        self._construct_regex_action_map()

    #regular expression for parsing recieved messages
    def _construct_regex_action_map(self):
        self.regex_action_map = [
            ('Help Request', self.help_regex, self.handle_help_request),
            ('Likes', self.likes, self.send_user_likes),
            ('Likes Rank', self.likesrank, self.send_user_likesrank),
            ('Imager', self.randomimage, self.send_random_image),
            ('Kicks', self.kicks, self.send_user_kicks),
            ('Info', self.groupinfo, self.send_group_info)
            ]

    #called by messages router when a message is recieved at the callback url
    def receive_message(self, message, attachments,senderid):
        for tag, regex, action in self.regex_action_map:
            m = regex.match(message)
            a = attachments
            s = senderid
            if m:
                self.logger.info('Received message of type %s; msg=\"%s\"', tag, message)
                if a:
                    action(m,a,s,message)
                else:
                    a = []
                    action(m,a,s,message)
                break

    #update the database from recent groupme messages
    def refresh_data_files(self):
        self.messages_collection.get_messages(self.refresh_days)
        self.messages_collection.update_names()
        self.messages_collection.get_likes()
        self.messages_collection.get_kicks()

    #resets can_randimg in the database for each user, related to limit random image in config
    def reset_media_usage(self):
        self.logger.info('Resetting random image..')
        self.messages_collection.can_randimg_reset()


    def send_group_info(self,m,a,s,text):
        self.send_message(self.messages_collection.get_group_info_message())

    #ask message collector for like stats for a user, the send them
    def send_user_likes(self,m,a,s,text):
        #if no one is tagged, get likes for sending user, otherwise get tagged user
        if a != []:
            rankstring = self.messages_collection.get_likes_message(a[0]['user_ids'][0])
        else:
            rankstring = self.messages_collection.get_likes_message(s)
        self.send_message(rankstring)
    
    #ask messages collector for top 12 users, then send
    def send_user_likesrank(self,m,a,s,text):
        self.send_message(self.messages_collection.get_rank_message())

    #ask messages collector for kick stats for a user, then send them
    def send_user_kicks(self,m,a,s,text):
        #if no one is tagged, get likes for sending user, otherwise get tagged user
        if a != []:
            rankstring = self.messages_collection.get_kicks_message(a[0]['user_ids'][0])
        else:
            rankstring = self.messages_collection.get_kicks_message(s)
        self.send_message(rankstring)

    #asks messages collector for a random image, then send the media
    def send_random_image(self,m,a,s,text):
        self.logger.info('Sending random image')

        if self.messages_collection.allowed_to_send(s):
            spaces = text.split()
            #if the messages is only one word long "!image", select from all images; if two words "!image 2015", select random image from that year
            if len(spaces) == 1:
                self.logger.info('Querying from all images')
                rand_media = self.messages_collection.get_media_attachment(s)
                print(rand_media)
                return_string = str(rand_media[2]) + " : " + (rand_media[1] if rand_media[1] else "")
                self.send_media(rand_media[0],return_string)
            elif len(spaces) == 2:
                try:
                    self.logger.info('Querying image from a year')
                    rand_media = self.messages_collection.get_range_media_attachment(s,int(spaces[1]))
                    print(rand_media)
                    return_string = str(rand_media[2]) + " : " + (rand_media[1] if rand_media[1] else "")
                    self.send_media(rand_media[0],return_string)
                except ValueError:
                    return

    def handle_help_request(self, m, a,s,text):
        help_message = 'Bot Commands\n'
        help_message += '!image for a random image\n'
        help_message += '!image [year] random image from a specified year\n'
        help_message += '!likes show your total likes\n'
        help_message += '!likes [tag] show total likes for a specified user\n'
        help_message += '!rank show top 10 users in likes\n'
        help_message += '!kicks show your total kick stats\n'
        help_message += '!kicks [tag] show kick stats for a specified user\n'
        help_message += '!info show various info for this group\n'

        self.send_message(help_message)

    def send_message(self, message):
        logmessage = message
        logmessage = logmessage.encode('ascii', 'ignore')
        self.logger.info("Sending message; msg=\"%s\"", message)

        data = {"bot_id": self.bot_id, "text": message}
        req = request.Request('https://api.groupme.com/v3/bots/post')
        req.add_header('Content-Type', 'application/json')
        time.sleep(1)  #prevents ordering issue in groupme if bot responds within the same second
        response = request.urlopen(req, json.dumps(data).encode('ascii'))
        response.close()
    
    def send_media(self, media,message=""):
        self.logger.info("Sending message of media")

        data = {"bot_id": self.bot_id, "attachments": [media], "text": message}
        req = request.Request('https://api.groupme.com/v3/bots/post')
        req.add_header('Content-Type', 'application/json')
        time.sleep(1) #prevents ordering issue in groupme if bot responds within the same second
        response = request.urlopen(req, json.dumps(data).encode('ascii'))
        response.close()


def initialize(bot_id=0, service_credentials=None):
    global bot
    bot = ExtBot(
        bot_id=bot_id)
    return bot

def listen(server_class=HTTPServer, handler_class=MessageRouter, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.getLogger('extlog').info('Listening for messages on port %d...', port)
    httpd.serve_forever()

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

def schduled_tasks():
    #bot.birthday_time()
    
    schedule.every().hour.do(run_threaded,bot.refresh_data_files)
    schedule.every().day.at("23:59").do(run_threaded,bot.reset_media_usage)

    while 1:
            schedule.run_pending()
            time.sleep(5)


