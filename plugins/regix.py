import os
import sys 
import math
import time
import asyncio 
import logging
import html
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot, get_configs
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
#from pyropatch.utils import unpack_new_file_id
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from .ftm_utils import create_source_link, create_target_link, add_ftm_caption, create_ftm_button, combine_buttons

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("please wait until previous task complete", show_alert=True)
    sts = STS(frwd_id)
    if not sts.verify():
      await message.answer("your are clicking on my old button", show_alert=True)
      return await message.message.delete()
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
      return await message.answer("In Target chat a task is progressing. please wait until task complete", show_alert=True)
    m = await msg_edit(message.message, "<code>verifying your data's, please wait.</code>")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    if not _bot:
      return await msg_edit(m, "<code>You didn't added any bot. Please add a bot using /settings !</code>", wait=True)
    try:
      client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
      return await m.edit(e)
    await msg_edit(m, "<code>processing..</code>")
    try: 
       await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
       await msg_edit(m, f"**Source chat may be a private channel / group. Use userbot (user must be member over there) or  if Make Your [Bot](t.me/{_bot['username']}) an admin over there**", retry_btn(frwd_id), True)
       return await stop(client, user)
    try:
       k = await client.send_message(i.TO, "Testing")
       await k.delete()
    except:
       await msg_edit(m, f"**Please Make Your [UserBot / Bot](t.me/{_bot['username']}) Admin In Target Channel With Full Permissions**", retry_btn(frwd_id), True)
       return await stop(client, user)
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>𝙵𝙾𝚁𝚆𝙰𝚁𝙳𝙸𝙽𝙶 𝚂𝚃𝙰𝚁𝚃𝙴𝙳 𝙱𝚈 <a href=https://t.me/ftmdeveloper>𝙵𝚃𝙼 𝙳𝙴𝚅𝙴𝙻𝙾𝙿𝙴𝚁</a></b>")
    sts.add(time=True)
    sleep = 0.5 if _bot['is_bot'] else 1.5
    await msg_edit(m, "<code>Processing...</code>") 
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    if locked:
        try:
          MSG = []
          pling=0
          await edit(m, 'Progressing', 10, sts)
          print(f"Starting Forwarding Process... From :{sts.get('FROM')} To: {sts.get('TO')} Totel: {sts.get('limit')} stats : {sts.get('skip')})")
          async for message in client.iter_messages(
            client,
            chat_id=sts.get('FROM'), 
            limit=int(sts.get('limit')), 
            offset=int(sts.get('skip')) if sts.get('skip') else 0
            ):
                if await is_cancelled(client, user, m, sts):
                   return
                if pling %20 == 0: 
                   await edit(m, 'Progressing', 10, sts)
                pling += 1
                sts.add('fetched')
                if message == "DUPLICATE":
                   sts.add('duplicate')
                   continue 
                elif message == "FILTERED":
                   sts.add('filtered')
                   continue 
                if message.empty or message.service:
                   sts.add('deleted')
                   continue

                # Apply filters
                filter_result = await should_forward_message(message, user)
                print(f"Message {message.id}: Filter result: {filter_result}")
                if message.photo and message.caption:
                    print(f"Message {message.id}: Has photo + caption (image+text)")
                elif message.photo:
                    print(f"Message {message.id}: Has photo only")
                elif message.text:
                    print(f"Message {message.id}: Has text only")

                if not filter_result:
                   print(f"Message {message.id}: FILTERED OUT")
                   sts.add('filtered')
                   continue
                else:
                   print(f"Message {message.id}: PASSED FILTER - will be forwarded")

                # Check for duplicates
                if await is_duplicate_message(message, user):
                   sts.add('duplicate')
                   continue
                if forward_tag:
                   MSG.append(message.id)
                   notcompleted = len(MSG)
                   completed = sts.get('total') - sts.get('fetched')
                   if ( notcompleted >= 100 
                        or completed <= 100): 
                      # Get FTM mode status
                      configs = await get_configs(user)
                      ftm_mode = configs.get('ftm_mode', False)
                      await forward(client, MSG, m, sts, protect, ftm_mode, _bot['is_bot'])
                      sts.add('total_files', notcompleted)
                      await asyncio.sleep(0.8)
                      MSG = []
                else:
                   new_caption = custom_caption(message, caption)
                   # Get FTM mode status
                   configs = await get_configs(user)
                   ftm_mode = configs.get('ftm_mode', False)
                   details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect, "ftm_mode": ftm_mode, "is_bot": _bot['is_bot']}
                   await copy(client, details, m, sts)
                   sts.add('total_files')
                   await asyncio.sleep(sleep) 
        except Exception as e:
            await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
            temp.IS_FRWD_CHAT.remove(sts.TO)
            return await stop(client, user)
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await send(client, user, "<b>🎉 𝙵𝙾𝚁𝚆𝙰𝚁𝙳𝙸𝙽𝙶 𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴𝙳 𝙱𝚈 🥀 <a href=https://t.me/ftmdeveloper>𝙵𝚃𝙼 𝙳𝙴𝚅𝙴𝙻𝙾𝙿𝙴𝚁</a>🥀</b>")
        await edit(m, 'Completed', "completed", sts) 
        await stop(client, user)

async def copy(bot, msg, m, sts):
   try:
     if 'button' in msg and msg['button']:
        # Check if FTM mode is enabled
        if msg.get('ftm_mode', False):
           source_link = create_source_link(sts.get('FROM'), msg['msg_id'])
           ftm_button = create_ftm_button(source_link)
           
           # Combine FTM button with existing button
           combined_button = combine_buttons(ftm_button, msg['button'])
           
           # Add FTM info to caption
           caption_with_ftm = add_ftm_caption(msg['caption'], source_link)
           
           sent_msg = await bot.send_message(
               sts.get('TO'), 
               caption_with_ftm, 
               reply_markup=combined_button, 
               protect_content=msg['protect']
           )
           
           # Update with target link if using userbot
           if sent_msg and not msg.get('is_bot', True):
              target_link = create_target_link(sts.get('TO'), sent_msg.id)
              updated_caption = add_ftm_caption(msg['caption'], source_link, target_link)
              try:
                 await sent_msg.edit_text(updated_caption, reply_markup=combined_button)
              except Exception as edit_e:
                 print(f"Failed to edit message with target link: {edit_e}")
        else:
           await bot.send_message(sts.get('TO'), msg['caption'], reply_markup=msg['button'], protect_content=msg['protect'])
     else:
        media_file_id = msg['media']
        if media_file_id:
           caption = msg['caption']
           # Handle potential encoding issues in caption
           if caption:
              try:
                 # Fix UTF-16-LE encoding issue by properly handling the caption
                 if isinstance(caption, bytes):
                    # If caption is bytes, decode it properly
                    try:
                       caption = caption.decode('utf-8', errors='ignore')
                    except:
                       caption = caption.decode('utf-8', errors='replace')
                 else:
                    # If caption is string, ensure it's clean UTF-8
                    caption = str(caption).encode('utf-8', errors='ignore').decode('utf-8')
              except Exception as enc_error:
                 print(f"Encoding error in caption: {enc_error}")
                 caption = "Caption encoding error"
           
           # Check if FTM mode is enabled
           if msg.get('ftm_mode', False):
              source_link = create_source_link(sts.get('FROM'), msg['msg_id'])
              ftm_button = create_ftm_button(source_link)
              
              # Add FTM info to caption
              caption_with_ftm = add_ftm_caption(caption, source_link)
              
              # Use copy_message with FTM features
              sent_msg = await bot.copy_message(
                  chat_id=sts.get('TO'),
                  from_chat_id=sts.get('FROM'),
                  message_id=msg['msg_id'],
                  caption=caption_with_ftm,
                  reply_markup=ftm_button,
                  protect_content=msg['protect']
              )
              
              # Update with target link if using userbot
              if sent_msg and not msg.get('is_bot', True):
                 target_link = create_target_link(sts.get('TO'), sent_msg.id)
                 updated_caption = add_ftm_caption(caption, source_link)
                 try:
                    await sent_msg.edit_caption(updated_caption, reply_markup=ftm_button)
                 except Exception as edit_e:
                    print(f"Failed to edit caption with target link: {edit_e}")
           else:
              # Normal copy without FTM
              await bot.copy_message(
                  chat_id=sts.get('TO'),
                  from_chat_id=sts.get('FROM'),
                  message_id=msg['msg_id'],
                  caption=caption,
                  protect_content=msg['protect']
              )
        else:
           # Handle potential encoding issues in message text
           text_content = msg['caption']
           if text_content:
              try:
                 text_content = str(text_content).encode('utf-8', errors='ignore').decode('utf-8')
              except (UnicodeDecodeError, UnicodeEncodeError) as enc_error:
                 print(f"Encoding error in text: {enc_error}")
                 text_content = "Text encoding error"
           
           # Check if FTM mode is enabled for text messages
           if msg.get('ftm_mode', False):
              source_link = create_source_link(sts.get('FROM'), msg['msg_id'])
              ftm_button = create_ftm_button(source_link)
              
              # Add FTM info to text content
              text_with_ftm = add_ftm_caption(text_content, source_link)
              
              sent_msg = await bot.send_message(
                  sts.get('TO'), 
                  text_with_ftm, 
                  reply_markup=ftm_button,
                  protect_content=msg['protect']
              )
              
              # Update with target link if using userbot
              if sent_msg and not msg.get('is_bot', True):
                 target_link = create_target_link(sts.get('TO'), sent_msg.id)
                 updated_text = add_ftm_caption(text_content, source_link, target_link)
                 try:
                    await sent_msg.edit_text(updated_text, reply_markup=ftm_button)
                 except Exception as edit_e:
                    print(f"Failed to edit text with target link: {edit_e}")
           else:
              await bot.send_message(sts.get('TO'), text_content, protect_content=msg['protect'])
     sts.add('total_files')
   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await copy(bot, msg, m, sts)
   except (UnicodeDecodeError, UnicodeEncodeError) as enc_error:
     print(f"Encoding error during copy: {enc_error}")
     sts.add('deleted')
   except Exception as e:
     print(f"ERROR copying message {msg.get('msg_id')}: {e}")
     import traceback
     traceback.print_exc()
     sts.add('deleted')

async def forward(bot, msg, m, sts, protect, ftm_mode=False, is_bot=True):
   try:
     if ftm_mode:
        # For FTM mode, copy messages individually to add buttons/captions
        for msg_id in msg:
           try:
              # Get the original message to process with FTM
              original_msg = await bot.get_messages(sts.get('FROM'), msg_id)
              if original_msg and not original_msg.empty and not original_msg.service:
                 source_link = create_source_link(sts.get('FROM'), msg_id)
                 ftm_button = create_ftm_button(source_link)

                 # Add FTM info to caption with source link
                 caption = original_msg.caption if original_msg.caption else ""
                 caption = add_ftm_caption(caption, source_link)

                 # Send the message first
                 sent_msg = await bot.copy_message(
                    chat_id=sts.get('TO'),
                    from_chat_id=sts.get('FROM'),
                    message_id=msg_id,
                    caption=caption,
                    reply_markup=ftm_button,
                    protect_content=protect
                 )

                 # Only update with target link if using userbot
                 if sent_msg and not is_bot:
                    target_link = create_target_link(sts.get('TO'), sent_msg.id)
                    updated_caption = add_ftm_caption(original_msg.caption if original_msg.caption else "", source_link, target_link)
                    try:
                       await sent_msg.edit_caption(
                          caption=updated_caption,
                          reply_markup=ftm_button
                       )
                    except Exception as edit_e:
                       print(f"Failed to edit caption with target link: {edit_e}")

              await asyncio.sleep(0.5)  # Small delay between messages
           except Exception as e:
              print(f"FTM forward individual error: {e}")
     else:
        # Normal forwarding without FTM
        await bot.forward_messages(
              chat_id=sts.get('TO'),
              from_chat_id=sts.get('FROM'), 
              protect_content=protect,
              message_ids=msg)

   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await forward(bot, msg, m, sts, protect, ftm_mode, is_bot)

PROGRESS = """
📈 Percetage: {0} %

♻️ Feched: {1}

♻️ Fowarded: {2}

♻️ Remaining: {3}

♻️ Stataus: {4}

⏳️ ETA: {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)

async def edit(msg, title, status, sts):
   i = sts.get(full=True)
   status = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
   percentage = "{:.0f}".format(float(i.fetched)*100/float(i.total))

   now = time.time()
   diff = int(now - i.start)
   speed = sts.divide(i.fetched, diff)
   elapsed_time = round(diff) * 1000
   time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
   estimated_total_time = elapsed_time + time_to_completion  
   progress = "◉{0}{1}".format(
       ''.join(["◉" for i in range(math.floor(int(percentage) / 10))]),
       ''.join(["◎" for i in range(10 - math.floor(int(percentage) / 10))]))
   button =  [[InlineKeyboardButton(title, f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
   estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
   estimated_total_time = estimated_total_time if estimated_total_time != '' else '0 s'

   text = TEXT.format(i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, status, percentage, estimated_total_time, progress)
   if status in ["cancelled", "completed"]:
      button.append(
         [InlineKeyboardButton('Support', url='https://t.me/ftmbotzsupportz'),
         InlineKeyboardButton('Updates', url='https://t.me/ftmbotz')]
         )
   else:
      button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
   await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      temp.IS_FRWD_CHAT.remove(sts.TO)
      await edit(msg, "Cancelled", "completed", sts)
      await send(client, user, "<b>❌ Forwarding Process Cancelled</b>")
      await stop(client, user)
      return True 
   return False 

async def should_forward_message(message, user_id):
    """Check if message should be forwarded based on user filters"""
    try:
        configs = await get_configs(user_id)
        filters = configs.get('filters', {})

        print(f"=== FILTER CHECK for Message {message.id} ===")
        print(f"User configs keys: {list(configs.keys())}")
        print(f"User filters: {filters}")
        print(f"Keywords config: {configs.get('keywords', [])}")
        print(f"Image+text filter: {filters.get('image_text', False)}")
        print(f"Message type: text={bool(message.text)}, photo={bool(message.photo)}, video={bool(message.video)}")
        print(f"Message caption: {bool(message.caption)}")
        
        if message.caption:
            try:
                caption_preview = str(message.caption).encode('utf-8', errors='ignore').decode('utf-8')[:50]
                print(f"Caption content: '{caption_preview}...'")
            except:
                print(f"Caption content: [ENCODING ERROR]")

        # Check image+text filter - this filter ONLY forwards messages with images (photos) AND text/caption
        if filters.get('image_text', False):
            print(f"Image+text filter is ENABLED - ONLY forwarding messages with BOTH images AND text/caption")
            has_image = bool(message.photo)
            has_text_or_caption = bool(message.caption and message.caption.strip()) or bool(message.text and message.text.strip())
            print(f"Has image: {has_image}, Has text/caption: {has_text_or_caption}")

            if has_image and has_text_or_caption:
                print(f"Message {message.id}: PASSED image+text filter (has both image and text/caption)")
                # Still need to check other filters like file size, keywords, etc.
            else:
                print(f"Message {message.id}: REJECTED by image+text filter (missing image or text/caption)")
                return False
        else:
            # If image+text filter is disabled, check individual message type filters
            print(f"Image+text filter is DISABLED, checking individual message type filters...")

            # Check message type filters - each type must be enabled to be forwarded
            message_allowed = False
            
            if message.text and filters.get('text', True):
                print(f"Message {message.id}: Text message - filter enabled")
                message_allowed = True
            elif message.photo and filters.get('photo', True):
                print(f"Message {message.id}: Photo message - filter enabled")
                message_allowed = True
            elif message.video and filters.get('video', True):
                print(f"Message {message.id}: Video message - filter enabled")
                message_allowed = True
            elif message.document and filters.get('document', True):
                print(f"Message {message.id}: Document message - filter enabled")
                message_allowed = True
            elif message.audio and filters.get('audio', True):
                print(f"Message {message.id}: Audio message - filter enabled")
                message_allowed = True
            elif message.voice and filters.get('voice', True):
                print(f"Message {message.id}: Voice message - filter enabled")
                message_allowed = True
            elif message.animation and filters.get('animation', True):
                print(f"Message {message.id}: Animation message - filter enabled")
                message_allowed = True
            elif message.sticker and filters.get('sticker', True):
                print(f"Message {message.id}: Sticker message - filter enabled")
                message_allowed = True
            elif message.poll and filters.get('poll', True):
                print(f"Message {message.id}: Poll message - filter enabled")
                message_allowed = True
            else:
                # Message type is not enabled in filters
                if message.text:
                    print(f"Message {message.id}: REJECTED - text message but text filter disabled")
                elif message.photo:
                    print(f"Message {message.id}: REJECTED - photo message but photo filter disabled")
                elif message.video:
                    print(f"Message {message.id}: REJECTED - video message but video filter disabled")
                elif message.document:
                    print(f"Message {message.id}: REJECTED - document message but document filter disabled")
                elif message.audio:
                    print(f"Message {message.id}: REJECTED - audio message but audio filter disabled")
                elif message.voice:
                    print(f"Message {message.id}: REJECTED - voice message but voice filter disabled")
                elif message.animation:
                    print(f"Message {message.id}: REJECTED - animation message but animation filter disabled")
                elif message.sticker:
                    print(f"Message {message.id}: REJECTED - sticker message but sticker filter disabled")
                elif message.poll:
                    print(f"Message {message.id}: REJECTED - poll message but poll filter disabled")
                return False
            
            if not message_allowed:
                return False

        # Check file size limit
        file_size_limit = configs.get('file_size', 0)
        size_limit_type = configs.get('size_limit')

        print(f"Checking file size limit: {file_size_limit} MB, type: {size_limit_type}")
        if file_size_limit > 0 and message.media:
            media = getattr(message, message.media.value, None)
            if media and hasattr(media, 'file_size'):
                file_size_mb = media.file_size / (1024 * 1024)  # Convert to MB
                print(f"File size: {file_size_mb:.2f} MB")

                if size_limit_type is True:  # More than
                    if file_size_mb <= file_size_limit:
                        print(f"Message {message.id}: REJECTED - file size {file_size_mb:.2f} MB <= {file_size_limit} MB")
                        return False
                elif size_limit_type is False:  # Less than
                    if file_size_mb >= file_size_limit:
                        print(f"Message {message.id}: REJECTED - file size {file_size_mb:.2f} MB >= {file_size_limit} MB")
                        return False

        # Check extension filters
        extensions = configs.get('extension')
        print(f"Extension filters: {extensions}")
        if extensions and message.document:
            file_name = getattr(message.document, 'file_name', '')
            if file_name:
                file_ext = file_name.split('.')[-1].lower()
                print(f"File extension: {file_ext}")
                if file_ext in [ext.lower().strip('.') for ext in extensions]:
                    print(f"Message {message.id}: REJECTED - extension {file_ext} is filtered")
                    return False

        # Check keyword filters
        keywords = configs.get('keywords', [])
        print(f"Keyword filters: {keywords}")
        if keywords and len(keywords) > 0:
            message_text = ""
            if message.text:
                message_text = message.text.lower()
            elif message.caption:
                message_text = message.caption.lower()
            elif message.document and hasattr(message.document, 'file_name'):
                message_text = message.document.file_name.lower()

            print(f"Message text for keyword check: '{message_text[:100]}...'")
            if message_text:
                # If keywords are set, message must contain at least one keyword
                keyword_found = any(keyword.lower().strip() in message_text for keyword in keywords if keyword.strip())
                print(f"Keyword found: {keyword_found}")
                if not keyword_found:
                    print(f"Message {message.id}: REJECTED - no keywords found")
                    return False
            else:
                print(f"Message {message.id}: REJECTED - no text content for keyword matching")
                return False

        print(f"Message {message.id}: PASSED all filters")
        return True
    
    except Exception as e:
        print(f"Error in should_forward_message: {e}")
        import traceback
        traceback.print_exc()
        return True  # Default to allow forwarding if there's an error

async def is_duplicate_message(message, user_id):
    """Check if message is duplicate based on user settings"""
    configs = await get_configs(user_id)

    if not configs.get('duplicate', True):
        return False  # Duplicate checking is disabled

    # Simple duplicate check based on file_id for media messages
    if message.media:
        media = getattr(message, message.media.value, None)
        if media and hasattr(media, 'file_unique_id'):
            # Here you could implement database storage of seen file IDs
            # For now, we'll return False to not block any messages
            # You can enhance this with proper duplicate tracking
            pass

    return False

async def stop(client, user):
   try:
     await client.stop()
   except:
     pass 
   await db.rmve_frwd(user)
   temp.forwardings -= 1
   temp.lock[user] = False 

async def send(bot, user, text):
   try:
      await bot.send_message(user, text=text)
   except:
      pass 

def custom_caption(message, caption):
    if message.caption:
       try:
          # Handle potential encoding issues - fix UTF-16-LE issue
          if isinstance(message.caption, bytes):
             try:
                old_caption = message.caption.decode('utf-8', errors='ignore')
             except:
                old_caption = message.caption.decode('utf-8', errors='replace')
          else:
             old_caption = str(message.caption).encode('utf-8', errors='ignore').decode('utf-8')
          old_caption = html.escape(old_caption)
       except Exception as enc_error:
          print(f"Encoding error in original caption: {enc_error}")
          old_caption = "Caption encoding error"

       if caption:
          try:
             if isinstance(caption, bytes):
                caption = caption.decode('utf-8', errors='ignore')
             new_caption = str(caption).replace('{caption}', old_caption)
          except Exception as enc_error:
             print(f"Encoding error in custom caption: {enc_error}")
             new_caption = old_caption
       else:
          new_caption = old_caption 
    else:
       if caption:
          try:
             if isinstance(caption, bytes):
                caption = caption.decode('utf-8', errors='ignore')
             new_caption = str(caption).encode('utf-8', errors='ignore').decode('utf-8')
          except Exception as enc_error:
             print(f"Encoding error in new caption: {enc_error}")
             new_caption = ""
       else:
          new_caption = ""
    return new_caption

def get_size(size):
  units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i]) 

def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ RETRY ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    await m.answer("Forwarding cancelled !", show_alert=True)

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify():
       fetched, forwarded, remaining = 0
    else:
       fetched, forwarded = sts.get('fetched'), sts.get('total_files')
       remaining = fetched - forwarded 
    est_time = TimeFormatter(milliseconds=est_time)
    est_time = est_time if (est_time != '' or status not in ['completed', 'cancelled']) else '0 s'
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()