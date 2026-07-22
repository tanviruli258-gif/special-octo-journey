import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import subprocess
import yt_dlp
import re

# আপনার টোকেন
BOT_TOKEN = "8548108469:AAFmnValzLDBJEiLOfLefWmjknVQ5swuuGI"
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার টেলিগ্রাম User ID
ADMIN_ID = 6468726869  

unique_users = set()
banned_users = set()
user_usage = {}
MAX_LIMIT = 5

# সাময়িকভাবে ইউজারের লিংক সেভ রাখার জন্য
user_links = {}

def is_allowed(user_id):
    if user_id in banned_users:
        return False, "❌ Banned!"
    if user_usage.get(user_id, 0) >= MAX_LIMIT and user_id != ADMIN_ID:
        return False, "⚠️ Limit Exceeded!"
    return True, ""

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    if user_id not in unique_users:
        unique_users.add(user_id)
        if user_id != ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"🔔 *New User!*\nName: {message.from_user.first_name}\nID: `{user_id}`", parse_mode='Markdown')
            except:
                pass

    welcome_text = "👋 Welcome!\n\nSend me a *YouTube, Facebook, or TikTok* link, or upload an *MP4* directly."
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# Admin Commands
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, f"📊 *Stats*\nUsers: {len(unique_users)}\nBanned: {len(banned_users)}", parse_mode='Markdown')

@bot.message_handler(commands=['ban', 'unban'])
def manage_users(message):
    if message.chat.id == ADMIN_ID:
        try:
            command = message.text.split()[0]
            target_id = int(message.text.split()[1])
            if command == '/ban':
                banned_users.add(target_id)
                bot.reply_to(message, f"✅ Banned: `{target_id}`", parse_mode='Markdown')
            elif command == '/unban':
                banned_users.discard(target_id)
                bot.reply_to(message, f"✅ Unbanned: `{target_id}`", parse_mode='Markdown')
        except:
            bot.reply_to(message, "⚠️ Format: `/ban user_id`")

# সোশ্যাল মিডিয়া লিংক হ্যান্ডলার
@bot.message_handler(func=lambda message: any(x in message.text.lower() for x in ['youtube.com', 'youtu.be', 'facebook.com', 'fb.watch', 'tiktok.com']))
def handle_social_links(message):
    user_id = message.chat.id
    
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    # লিংকটি মেমোরিতে সেভ রাখা
    user_links[user_id] = message.text
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎥 3GP", callback_data="fmt_3gp"),
        InlineKeyboardButton("🎵 Audio", callback_data="fmt_audio")
    )
    bot.reply_to(message, "Choose format:", reply_markup=markup)

# বাটন ক্লিক হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: call.data in ['fmt_3gp', 'fmt_audio'])
def process_link_callback(call):
    user_id = call.message.chat.id
    
    if user_id not in user_links:
        bot.answer_callback_query(call.id, "❌ Link expired. Send again.")
        return
        
    url = user_links[user_id]
    format_type = call.data
    
    # বাটন রিমুভ করে স্ট্যাটাস দেওয়া
    bot.edit_message_text("⏳ Downloading...", chat_id=user_id, message_id=call.message.message_id)
    
    raw_file = f"{user_id}_raw.mp4"
    output_file = f"{user_id}.3gp" if format_type == 'fmt_3gp' else f"{user_id}.mp3"
    
    try:
        # yt-dlp দিয়ে ডাউনলোড
        ydl_opts = {
            'outtmpl': raw_file,
            'format': 'best',
            'max_filesize': 50000000, # 50MB লিমিট
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        bot.edit_message_text("🔄 Converting...", chat_id=user_id, message_id=call.message.message_id)
        
        # ফরম্যাট অনুযায়ী FFmpeg কমান্ড
        if format_type == 'fmt_3gp':
            command = ["ffmpeg", "-y", "-i", raw_file, "-c:v", "mpeg4", "-c:a", "aac", "-s", "352x288", "-b:v", "400k", "-b:a", "64k", "-ar", "8000", "-ac", "1", output_file]
        else:
            command = ["ffmpeg", "-y", "-i", raw_file, "-q:a", "0", "-map", "a", output_file]
            
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            bot.edit_message_text("❌ Conversion Error!", chat_id=user_id, message_id=call.message.message_id)
            if user_id != ADMIN_ID:
                bot.send_message(ADMIN_ID, f"⚠️ Error by `{user_id}`:\n`{result.stderr[-200:]}`", parse_mode='Markdown')
            return
            
        bot.edit_message_text("✅ Uploading...", chat_id=user_id, message_id=call.message.message_id)
        
        # ইউজারের লিমিট আপডেট
        user_usage[user_id] = user_usage.get(user_id, 0) + 1
        rem = MAX_LIMIT - user_usage[user_id]
        
        caption = "🎬 Done!"
        if user_id != ADMIN_ID:
            caption += f"\n📊 Limit left: {rem}"
            
        with open(output_file, 'rb') as f:
            if format_type == 'fmt_3gp':
                bot.send_video(user_id, f, caption=caption)
            else:
                bot.send_audio(user_id, f, caption=caption)
                
        bot.delete_message(user_id, call.message.message_id)
        del user_links[user_id] # মেমোরি থেকে লিংক ক্লিয়ার
        
    except Exception as e:
        bot.edit_message_text("❌ System Error!", chat_id=user_id, message_id=call.message.message_id)
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"⚠️ Error:\n`{e}`", parse_mode='Markdown')
    finally:
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(output_file): os.remove(output_file)

# সরাসরি আপলোড করা MP4 ফাইলের জন্য (আগের ফাংশন)
@bot.message_handler(content_types=['video', 'document'])
def handle_direct_video(message):
    user_id = message.chat.id
    
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    unique_users.add(user_id)
    input_file = f"{user_id}.mp4"
    output_file = f"{user_id}.3gp"
    
    status_msg = bot.reply_to(message, "⏳ Downloading...")
    
    try:
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("🔄 Converting...", chat_id=user_id, message_id=status_msg.message_id)
        
        command = ["ffmpeg", "-y", "-i", input_file, "-c:v", "mpeg4", "-c:a", "aac", "-s", "352x288", "-b:v", "400k", "-b:a", "64k", "-ar", "8000", "-ac", "1", output_file]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            bot.edit_message_text("❌ Error!", chat_id=user_id, message_id=status_msg.message_id)
            return
            
        bot.edit_message_text("✅ Uploading...", chat_id=user_id, message_id=status_msg.message_id)
        
        user_usage[user_id] = user_usage.get(user_id, 0) + 1
        rem = MAX_LIMIT - user_usage[user_id]
        
        caption = "🎬 Done!"
        if user_id != ADMIN_ID:
            caption += f"\n📊 Limit left: {rem}"
            
        with open(output_file, 'rb') as video:
            bot.send_video(user_id, video, caption=caption)
            
        bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text("❌ Error!", chat_id=user_id, message_id=status_msg.message_id)
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

bot.polling(none_stop=True)
