import asyncio
import logging 
import os
import logging.config
from database import db 
from config import Config  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={
                "root": "plugins"
            },
            workers=50,
            bot_token=Config.BOT_TOKEN
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        text = "**๏[-ิ_•ิ]๏ bot restarted !**"
        logging.info(text)
        success = failed = 0
        
        # Send restart message to all users (not just forwarding users)
        all_users = await db.get_all_users()
        async for user in all_users:
           chat_id = user['id']
           try:
              await self.send_message(chat_id, text)
              success += 1
           except FloodWait as e:
              await asyncio.sleep(e.value + 1)
              try:
                 await self.send_message(chat_id, text)
                 success += 1
              except Exception:
                 failed += 1
           except Exception:
              failed += 1 
        
        # Also send to owner
        for owner_id in Config.OWNER_ID:
           try:
              await self.send_message(owner_id, text)
           except Exception:
              pass
        
        # Clear all forwarding sessions
        await db.rmve_frwd(all=True)
        if (success + failed) != 0:
           logging.info(f"Restart message status - "
                 f"success: {success}, "
                 f"failed: {failed}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)
