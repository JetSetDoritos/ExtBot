# ExtBot

## **Description**

A GroupMe bot written in Python that uses GroupMe's REST API to provide like and kick stats, as well as posting random images.  Messages are stored using SQLite.

This has been tested in a group with over 250k messages.

This project was possible by [Chomps Bot](https://github.com/noeltrivedi/beer_pong_bot) and [GroupMe Analytics](https://github.com/octohub/GroupMeAnalytics), which were used to learn GroupMe's bot and application APIs accordingly.

## **Setup**

0. Install required python libraries in requirements.txt (schedule, requests)

1. In the data folder, create a copy or rename the example config file to config.json

2. Sign into dev.groupme.com with your GroupMe account

3. In the "Bots" tab create a bot in your group, set your callback url with the IP:port you will be hosting the bot on, also a name and optional photo

4. Copy the Bot ID and Group ID into the config file, also set the listening port

5. At the top of the dev.groupme.com page click "Access Token" and copy it to the config file

6. Run rebuild_database.py to create the local database of your groups messages (this may take some time! downloading 250k messages takes around 30 minutes!)

7. Edit the config file as you see fit, though the default settings are what worked best in my group.

8. Run run.py to start the bot :)

*NOTE: you may need to rerun rebuild_database every once in a great while, messages older than the "refresh_days" will not be seen, but this should be very marginal.*

## **Config File**
__bot_id__ : Your bot id from dev.groupme.com bots tab

__listening_port__ : The port you are hosting the bot on

__api_key__ : your api key from dev.groupme.com

__group_id__ : the group id the bot is in from dev.groupme.com bots tab

__disable_image__ : enable/disable the !image function

__like_threshold__ : when !image is ran, this is the minimim number for the image it picks

__year_like_threshold__ : when !image [year] is ran, this is the minimim number for the image it picks

__limit_image__ : limit !image to one per day per user (this prevents so much spam)

__refresh_days__ : the bot refreshes messages every hour, this is the amount of days back it checks,refreshing too many messages can use a lot of API calls and take much longer, though there is no documented API limit my calls started failing around ~2,500 within one hour, this days limit reduces the API calls to less than a dozen per hour usually

## **Bot Usage**

| Command  | Function |
| ------------- | ------------- |
| !image  | Post a random image previously posted in the chat, along with the original poster and message text  |
| !image [year]  | !image, randomly picks from a specified year, ignores the year if there are no posts for that year  |
| !likes     | Posts the total number of likes and rank for that user |
| !likes [tag user] | Posts the total number of likes and rank for the tagged user |
| !rank | Posts a leaderboard of the top 12 users in terms of likes |
| !kicks | Posts the total number of times kicked/times kicker for that user, might not be intresting for Locked groups as only the owner can kick |
| !kicks [tag user] | Posts the total number of times kicked/times kicker for the tagged user, might not be intresting for Locked groups as only the owner can kick |
| !info | Posts group info such as total number of messages, group creation date, group creator, and minimum likes for image from the config file |

## **Screenshots**

**!info**

<img src="../readme_images/example_images/info_example.png?raw=true" width="500">

**!likes**

<img src="../readme_images/example_images/likes_example.png?raw=true" width="500">

**!rank**

<img src="../readme_images/example_images/rank_example.png?raw=true" width="500">

**!kicks**

<img src="../readme_images/example_images/kicks_example.png?raw=true" width="500">

**!image**

<img src="../readme_images/example_images/image_example.png?raw=true" width="500">


## **Adding Functions**

I'll document how to add your own functionality later
