# ExtBot

## **Description**

A GroupMe bot written in Python that uses GroupMe's REST API to provide like and kick stats, as well as posting random images.  Messages are stored using SQLite.

## **Setup**

TODO: 
Fill out the config file
Run buildMessages.py
Run run.py

## **Config File**

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



## **Adding Functions**

