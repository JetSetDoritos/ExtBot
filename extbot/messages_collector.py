import requests
import sys
import json
import time
import os
import logging
import csv
from random import randint
import sqlite3
import ast
import datetime

#establishes config file paths
config_path = os.path.join('.','data','config.json')

class MessagesCollector():

    def __init__(self):
        self.logger = logging.getLogger('extlog')
        self.dbpath = './data/exdatabase.sqlite3'

        #grabs values from config file
        with open(config_path) as config_file:
            config = json.load(config_file)
        self.like_threshold = config['like_threshold']
        self.year_like_threshold = config['year_like_threshold']
        self.limit_image = config['limit_image']       
        self.api_key = config['api_key']
        self.group_id = config['group_id']
        self.image_disabled = config['disable_image'] 

    #creates/updates messages in the local database, pass in how many days back to scan, 0 to scan every message (can take a long time!)
    def get_messages(self,days_back=0):
        apikey = self.api_key
        groupid = self.group_id
        db = sqlite3.connect(self.dbpath)
        
        cursor = db.cursor()

        #creates tables if they dont exist
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    image_url TEXT,
                    other_id TEXT unique,
                    likes INTEGER,
                    rank INTEGER,
                    date_added INTEGER,
                    self_likes INTEGER,
                    times_kicked INTEGER,
                    times_kicker INTEGER,
                    can_randimage INTEGER
                    )
            ''')
        db.commit()
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages(
                    id TEXT PRIMARY KEY,
                    created_at INTEGER,
                    text TEXT,
                    favorites INTEGER,
                    favorited_by TEXT,
                    is_bot INTEGER,
                    sender_id TEXT,
                    system TEXT,
                    has_image INTEGER,
                    has_loci INTEGER,
                    has_tag INTEGER,
                    attachments TEXT,
                    event TEXT,
                    CONSTRAINT fk_users
                        FOREIGN KEY (sender_id)
                        REFERENCES users(id)
                )
            ''')

        #this line can probably be removed
        #cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        db.commit()
        print(cursor.fetchall())


        #gets group data, puts group members in users table
        response = requests.get('https://api.groupme.com/v3/groups/' + groupid + '?token='+ apikey)
        currentgroup = response.json()['response']
        members = currentgroup['members']
        for m in members:
            cursor.execute('''INSERT OR IGNORE INTO users(id,name,image_url,other_id,likes,self_likes,times_kicked,times_kicker,can_randimage)
                              VALUES(?,?,?,?,?,?,?,?,?);''', (m['user_id'],m['nickname'],m['image_url'],m['id'],0,0,0,0,1)
            
            )
            db.commit()

        message_id = 0

        #finds stopping point for get messages if a set amount of days
        #finds the messages thats closest to the desired unix time, sets it as the stopping point
        if days_back > 0:
            timegap = time.time() - (86400 * days_back)
            cursor.execute('''SELECT
                                id,
                                sequence,
                                created_at
                              FROM
                                messages
                              WHERE
                                created_at < ?
                              LIMIT 1
                            ''' , (timegap,)
            )
            continue_to = cursor.fetchone()
            print("continue: "+ str(continue_to))
            ending_message = continue_to[0]
        else:
            cursor.execute('''SELECT
                                id,
                                sequence,
                                created_at
                              FROM
                                messages
                              ORDER BY
                                created_at ASC
                              LIMIT 1
                            '''
            )
            continue_to = cursor.fetchone()
            print("continue: "+ str(continue_to))
            ending_message = continue_to[0]


        #while the current message is less than the desired message, request 100 messages at a time to update in the database
        while 1:
            params = {
                    # Get maximum number of messages at a time
                    'limit': 100,
                }
            if message_id != 0:
                params['before_id'] = message_id
            response = requests.get('https://api.groupme.com/v3/groups/%s/messages?token=%s' % (groupid, apikey), params=params)

            messages = response.json()['response']['messages']
            for m in messages:
                sysval = 0
                is_bot = 0
                
                #if a user that is no longer in the group, add to users table
                cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE id="'+ m['sender_id'] +'" LIMIT 1);')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''INSERT OR IGNORE INTO users(id,name,likes,self_likes,times_kicked,times_kicker,can_randimage)
                              VALUES(?,?,?,?,?,?,?)''', (m['sender_id'],m['name'],0,0,0,0,1))
                    db.commit()

                if m['system']:
                    sysval = 1
                if m['sender_type'] == "bot":
                    is_bot = 1
                
                hasimage = 0
                hasloci = 0
                hastag = 0
                for a in m['attachments']:
                    if a['type'] == 'image':
                        hasimage = 1
                    if a['type'] == 'video':
                        hasimage = 1
                    if a['type'] == 'mentions':
                        hastag = 1
                #case for if the message is a system message, has a few different/missing  attributes
                if sysval == 0:
                    cursor.execute('''INSERT OR REPLACE INTO messages(id,created_at,favorites,favorited_by,sender_id,system,has_image,has_loci,has_tag,attachments,text,is_bot)
                                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (m['id'],int(m['created_at']),len(m['favorited_by']),str(m['favorited_by']), str(m['sender_id']),sysval,hasimage,hasloci,hastag,str(m['attachments']),m['text'],is_bot)
                    )
                else:
                    if 'event' in m:
                        cursor.execute('''INSERT OR REPLACE INTO messages(id,created_at,favorites,favorited_by,sender_id,system,has_image,has_loci,has_tag,attachments,text,event,is_bot)
                                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''', (m['id'],int(m['created_at']),len(m['favorited_by']),str(m['favorited_by']), str(m['sender_id']),sysval,hasimage,hasloci,hastag,str(m['attachments']),m['text'],str(m['event']),0)
                        )
                if(m['id'] == ending_message):
                    db.commit()
                    db.close
                    self.logger.info('Refresh completed successfully.')
                    return
            db.commit()
            message_id = messages[-1]['id']

    #returns group info like total messages, date created, and other non-sensitive config file info
    def get_group_info_message(self):
        response = requests.get('https://api.groupme.com/v3/groups/' + self.group_id + '?token='+ self.api_key)
        currentgroup = response.json()['response']
        return_string = "[Group Information]\n"
        return_string += "Total messages: " + str(currentgroup['messages']['count']) + "\n"
        return_string += "Date created: " + str(datetime.datetime.utcfromtimestamp(currentgroup['created_at']).strftime('%m-%d-%Y | %H:%M:%S UTC')) + "\n"
        return_string += "Created by: " + self.string_name(currentgroup['creator_user_id']) + "\n"
        return_string += "Min likes for !image: " + str(self.like_threshold) + "\n" 
        return_string += "Min likes for year !image: " + str(self.year_like_threshold) + "\n"
        return return_string

        
    #processes the database to calculate likes for each user
    def get_likes(self):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor_writer = db.cursor()

        #iterate through each user in the users table, then iterate through all their messages and total their likes
        for u in cursor.execute("SELECT id FROM users;"):
            currentuser = u[0]
            currentlikes = 0
            currentSlikes = 0
            for m in cursor2.execute("SELECT favorites,favorited_by FROM messages WHERE sender_id = ?;",(currentuser,)):
                currentlikes += int(m[0])
                favby = ast.literal_eval(m[1])
                if currentuser in favby:
                    currentSlikes += 1
            cursor_writer.execute("UPDATE users SET likes=?,self_likes=? WHERE id=?;", (currentlikes,currentSlikes,currentuser))
        db.commit()
        
        #sort the users table by likes, then give each user their ranking in order
        rank = 1
        for u in cursor.execute("SELECT id,likes FROM users ORDER BY likes DESC;"):
            cursor_writer.execute("UPDATE users SET rank=? WHERE id = ?;", (rank,u[0],))
            rank += 1
        db.commit()
        db.close()
        self.logger.info('Like data updated..')

    #processes the database to find the times kicked/times kicker
    def get_kicks(self):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        cursor2 = db.cursor()
        
        #set all users kicks/likes to zero
        cursor.execute("UPDATE users SET times_kicker=0,times_kicked=0;")

        #iterate through all messages with event attribute and increment kick data if present
        for m in cursor.execute("SELECT event FROM messages WHERE event IS NOT NULL"):
            event = ast.literal_eval(m[0])
            
            if event['type'] == "membership.notifications.removed":
                kicker = event['data']['remover_user']['id']
                cursor2.execute("UPDATE users SET times_kicker = times_kicker + 1 WHERE id = ? ;", (str(kicker),))
                #db.commit()
                kicked = event['data']['removed_user']['id']
                cursor2.execute("UPDATE users SET times_kicked = times_kicked + 1 WHERE id = ?;",(str(kicked),))
                #db.commit()
            
        db.commit()
        db.close()
        self.logger.info('Kick data updated..')

    #update nicknames for all users currently in the group
    def update_names(self):
        db = sqlite3.connect(self.dbpath)
        apikey = self.api_key
        groupid = self.group_id
        cursor = db.cursor()

        response = requests.get('https://api.groupme.com/v3/groups/' + groupid + '?token='+ apikey)
        #self.logger.info('Server Response: ' + response)
        currentgroup = response.json()['response']
        members = currentgroup['members']

        #for each member in the group, update their nickname in the database
        for m in members:
            cursor.execute("UPDATE users SET name=?,image_url=? WHERE id = ?;",(m['nickname'],m['image_url'],m['user_id']))
        
        db.commit()
        db.close()
        self.logger.info('Nicknames updated..')

    #sets can_randimage in the database to 1 for all users, related to limiting 1 image per day per user
    def can_randimg_reset(self):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        self.logger.info('m_c resetting can image')
        cursor.execute("UPDATE users SET can_randimage=1;")
        db.commit()
        db.close()
        self.logger.info('Random image usage reset..')

    #querys the database for the likes for a specified user, returns the likes message string
    def get_likes_message(self,senderid):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        
        cursor.execute("SELECT name,likes,self_likes,rank FROM users WHERE id = ?;", (senderid,))
        u = cursor.fetchone()

        db.close()
        return "Like stats for: " + u[0] + "\nLikes: " + str(u[1]) + "\nSelf Likes: " + str(u[2]) + "\nRank: " + str(u[3])

    #querys the database for users in order of like rank, returns a string of the top 12
    def get_rank_message(self):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        
        returnString = ""
        for u in cursor.execute("SELECT rank,name,likes FROM users ORDER BY rank ASC LIMIT 12"):
            returnString += str(u[0]) + ". " + str(u[1]) + " : " + str(u[2]) + "\n"
        
        db.close()
        return returnString

    #querys the database for a users kick stats, returns string 
    def get_kicks_message(self,senderid):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()

        cursor.execute("SELECT name,times_kicked,times_kicker FROM users WHERE id = ?;", (senderid,))
        u = cursor.fetchone()

        db.close()
        return "Kick stats for: " + str(u[0]) + "\nKicked: " + str(u[1]) + "\nKicked Others: " + str(u[2])
    
    #returns a users nickname as a string from their user id
    def string_name(self,senderid):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM users WHERE id=?;",(senderid,))
        u = cursor.fetchone()

        db.close()
        return u[0]

    #returns boolean based on can_randimage for a user in the database, related to limiting image daily
    #returns true if user has no used !image on that day
    def allowed_to_send(self,senderid):
        if self.image_disabled:
            self.logger.info('Image function is disabled in the config file.')
            return False
        if self.limit_image:
            db = sqlite3.connect(self.dbpath)
            cursor = db.cursor()

            cursor.execute("SELECT can_randimage FROM users WHERE id = ?;", (senderid,))
            u = cursor.fetchone()
            db.close()
            if u[0] == 1:
                return True
            else:
                self.logger.info('User has already used their daily image.')
                return False
        else:
            return True

    #gets a image or video url from a previously posted message at random
    #returns tuple of (attachment, message text, message sender)
    def get_media_attachment(self,senderid):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()


        cursor.execute("SELECT attachments,text,sender_id FROM messages WHERE has_image=1 AND favorites>? AND is_bot=0 ORDER BY Random();",(self.like_threshold,))
        m = cursor.fetchone()
        attachments = ast.literal_eval(m[0])
        print(m[2])
        for a in attachments:
            self.logger.info(a)
            if a['type'] == "image":
                cursor.execute("UPDATE users SET can_randimage=0 WHERE id=?;",(senderid,))
                db.commit()
                db.close()
                return (a,m[1],self.string_name(m[2]))
            elif a['type'] == "video":
                cursor.execute("UPDATE users SET can_randimage=0 WHERE id=?;",(senderid,))
                db.commit()
                db.close()
                return (a,m[1],self.string_name(m[2]))

    #gets a image or video url from a previously posted message of a certian year at random
    #returns tuple of (attachment, message text, message sender)
    def get_range_media_attachment(self,senderid,year):
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()

        #determines d1(min date) and d2(max date) for the message
        d1=datetime.date(int(year),1,1)
        d2=datetime.date(int(year)+1,1,1)
        #converts to unix timestamp
        d1u = time.mktime(d1.timetuple())
        d2u = time.mktime(d2.timetuple())

        cursor.execute("SELECT attachments,text,sender_id FROM messages WHERE has_image=1 AND is_bot=0 AND created_at>? AND created_at<? AND favorites>? ORDER BY Random();",(d1u,d2u,self.year_like_threshold,))
        temp = cursor.fetchone()

        #if nothing is found for the requested year, a random image is returned without the year constraint
        if temp is None:
            db.close()
            self.logger.info('Invalid year, sending message without specified year.')
            return self.get_media_attachment(senderid)
        else:
            #return the image or video, could be changed to or statement
            attachments = ast.literal_eval(temp[0])
            for a in attachments:
                self.logger.info(str(a))

                if a['type'] == "image":
                    cursor.execute("UPDATE users SET can_randimage=0 WHERE id=?;",(senderid,))
                    db.commit()
                    db.close()

                    return (a,temp[1],self.string_name(temp[2]))
                elif a['type'] == "video":
                    cursor.execute("UPDATE users SET can_randimage=0 WHERE id=?;",(senderid,))
                    db.commit()
                    db.close()
                    return (a,temp[1],self.string_name(temp[2]))
        
        
                    
                
            