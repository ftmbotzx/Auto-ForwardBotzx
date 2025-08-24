import os
import sys
import asyncio 
import logging
from database import db, mongodb_version
from config import Config, temp
from platform import python_version
from translation import Translation
from pyrogram import Client, filters, enums, __version__ as pyrogram_version
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument

# Setup logging
logger = logging.getLogger(__name__)

main_buttons = [[
        InlineKeyboardButton('Main Channel', url='https://t.me/ftmbotz')
        ],[
        InlineKeyboardButton('📜 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ', url='https://t.me/ftmbotzsupportz'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ  ', url='https://t.me/ftmbotz')
        ],[
        InlineKeyboardButton('🙋‍♂️ ʜᴇʟᴘ', callback_data='help'),
        InlineKeyboardButton('💁‍♂️ ᴀʙᴏᴜᴛ ', callback_data='about')
        ],[
        InlineKeyboardButton('⚙️ sᴇᴛᴛɪɴɢs ⚙️', callback_data='settings#main')
        ]]


#===================Start Function===================#

@Client.on_message(filters.private & filters.command(['start']))
async def start(client, message):
    user = message.from_user
    logger.info(f"Start command from user {user.id} ({user.first_name})")
    
    try:
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
            logger.info(f"New user added: {user.id}")
        
        reply_markup = InlineKeyboardMarkup(main_buttons)
        jishubotz = await message.reply_sticker("CAACAgUAAxkBAAECEEBlLA-nYcsWmsNWgE8-xqIkriCWAgACJwEAAsiUZBTiPWKAkUSmmh4E")
        await asyncio.sleep(2)
        await jishubotz.delete()
        text=Translation.START_TXT.format(user.mention)
        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            quote=True
        )
        logger.info(f"Start message sent to user {user.id}")
    except Exception as e:
        logger.error(f"Error in start command for user {user.id}: {e}", exc_info=True)
        await message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='back')]])
        )



#==================Restart Function==================#

@Client.on_message(filters.private & filters.command(['restart', "r"]) & filters.user(Config.OWNER_ID))
async def restart(client, message):
    msg = await message.reply_text(
        text="<i>Trying To Restarting.....</i>",
        quote=True
    )
    await asyncio.sleep(5)
    await msg.edit("<i>Server Restarted Successfully ✅</i>")
    os.execl(sys.executable, sys.executable, *sys.argv)
    


#==================Callback Functions==================#

@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    user_id = query.from_user.id
    logger.info(f"Help callback from user {user_id}")
    
    try:
        await query.message.edit_text(
            text=Translation.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(
                [[
                InlineKeyboardButton('🛠️ How To Use Me 🛠️', callback_data='how_to_use')
                ],[
                InlineKeyboardButton('⚙️ Settings ⚙️', callback_data='settings#main'),
                InlineKeyboardButton('📊 Stats 📊', callback_data='status')
                ],[
                InlineKeyboardButton('🔙 Back', callback_data='back')
                ]]
            ))
        logger.debug(f"Help message sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in help callback for user {user_id}: {e}", exc_info=True)



@Client.on_callback_query(filters.regex(r'^how_to_use'))
async def how_to_use(bot, query):
    user_id = query.from_user.id
    logger.info(f"How to use callback from user {user_id}")
    
    try:
        await query.message.edit_text(
            text=Translation.HOW_USE_TXT,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='help')]]),
            disable_web_page_preview=True
        )
        logger.debug(f"How to use message sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in how_to_use callback for user {user_id}: {e}", exc_info=True)



@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    user_id = query.from_user.id
    logger.info(f"Back callback from user {user_id}")
    
    try:
        reply_markup = InlineKeyboardMarkup(main_buttons)
        await query.message.edit_text(
           reply_markup=reply_markup,
           text=Translation.START_TXT.format(
                    query.from_user.first_name))
        logger.debug(f"Back to main menu for user {user_id}")
    except Exception as e:
        logger.error(f"Error in back callback for user {user_id}: {e}", exc_info=True)



@Client.on_callback_query(filters.regex(r'^about'))
async def about(bot, query):
    user_id = query.from_user.id
    logger.info(f"About callback from user {user_id}")
    
    try:
        await query.message.edit_text(
            text=Translation.ABOUT_TXT.format(bot.me.mention),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='back')]]),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
        )
        logger.debug(f"About message sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in about callback for user {user_id}: {e}", exc_info=True)



@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    user_id = query.from_user.id
    logger.info(f"Status callback from user {user_id}")
    
    try:
        users_count, bots_count = await db.total_users_bots_count()
        total_channels = await db.total_channels()
        await query.message.edit_text(
            text=Translation.STATUS_TXT.format(users_count, bots_count, temp.forwardings, total_channels, temp.BANNED_USERS ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='help')]]),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
        logger.debug(f"Status message sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in status callback for user {user_id}: {e}", exc_info=True)
    

