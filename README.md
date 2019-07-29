# ExtBot

## **Description**

A GroupMe bot written in Python that uses GroupMe's REST API to provide like and kick stats, as well as posting random images.  Messages are stored using SQLite.

## **Setup**

TODO: 
Fill out the config file
Run buildMessages.py
Run run.py

## **Config File**
bot_id : Your bot id from dev.groupme.com bots tab

listening_port : The port you are hosting the bot on

api_key : your api key from dev.groupme.com applications tab

group_id : the group id the bot is in from dev.groupme.com bots tab

disable_image : enable/disable the !image function

like_threshold : when !image is ran, this is the minimim number for the image it picks

year_like_threshold : when !image [year] is ran, this is the minimim number for the image it picks

limit_image : limit !image to one per day per user (this prevents so much spam)

refresh_days : the bot refreshes messages every hour, this is the amount of days back it checks,refreshing too many messages can use a lot of API calls and take much longer, though there is no documented API limit my calls started failing around ~2,500 within one hour, this days limit reduces the API calls to less than a dozen per hour usually

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

<img src="../image_hosting/example_images/info_example.png?raw=true" width="500">

**!likes**

<img src="../image_hosting/example_images/likes_example.png?raw=true" width="500">

**!rank**

<img src="../image_hosting/example_images/rank_example.png?raw=true" width="500">

**!kicks**

<img src="../image_hosting/example_images/kicks_example.png?raw=true" width="500">

**!image**

<img src="../image_hosting/example_images/image_example.png?raw=true" width="500">


## **Adding Functions**

