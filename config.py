from os import environ 

class Config:
    API_ID = environ.get("API_ID", "28776072")
    API_HASH = environ.get("API_HASH", "b3a786dce1f4e7d56674b7cadfde3c9d")
    BOT_TOKEN = environ.get("BOT_TOKEN", "8101859818:AAE0HsHqu0FnclTX1JVG65fot5EwaQNhmJg") 
    BOT_SESSION = environ.get("BOT_SESSION", "forward-bot") 
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://ftm:ftm@cluster0.9a4gw2t.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DATABASE_NAME = environ.get("DATABASE_NAME", "forward-bot")
    OWNER_ID = [int(id) for id in environ.get("OWNER_ID", '7711039923').split()]

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
