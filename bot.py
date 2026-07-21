import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import subprocess

# আপনার টোকেন
BOT_TOKEN = "8548108469:AAFmnValzLDBJEiLOfLefWmjknVQ5swuuGI"
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার টেলিগ্রাম User ID (এখানে আপনার আইডি বসান)
ADMIN_ID = 7392861032  

unique_users = set()
banned_users = set()
user_usage = {}
MAX_LIMIT = 5  # একজন ইউজার কয়টি ভিডিও কনভার্ট করতে পারবে

# ইউজার চেক করার ফাংশন
def is_allowed(user_id):
    if user_id in banned_users:
        return False, "❌ আপনি এই বট থেকে ব্যান হয়েছেন!"
    if user_usage.get(user_id, 0) >= MAX_LIMIT and user_id != ADMIN_ID:
        return False, "⚠️ আপনার ভিডিও কনভার্ট করার লিমিট শেষ হয়ে গেছে!"
    return True, ""

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # ব্যান বা লিমিট চেক
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    if user_id not in unique_users:
        unique_users.add(user_id)
        if user_id != ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"🔔 *নতুন ইউজার!*\nনাম: {message.from_user.first_name}\nআইডি: `{user_id}`", parse_mode='Markdown')
            except:
                pass

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🧑‍💻 Developer", url="https://t.me/your_telegram_username")) 
    
    welcome_text = (
        f"স্বাগতম *{message.from_user.first_name}*! 👋\n\n"
        "আমি একটি প্রোফেশনাল ভিডিও কনভার্টার বট। আমাকে যেকোনো *MP4* ভিডিও দিন, "
        "আমি সেটি দ্রুত *3GP* ফরম্যাটে কনভার্ট করে দেব।\n\n"
        "💡 _অপেক্ষাকৃত ছোট সাইজের ভিডিও দিন যাতে দ্রুত কনভার্ট হয়।_"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

# অ্যাডমিন প্যানেল: স্ট্যাটাস
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, f"📊 *বটের বর্তমান পরিসংখ্যান:*\n\nমোট ইউজার: {len(unique_users)} জন\nব্যানড ইউজার: {len(banned_users)} জন", parse_mode='Markdown')

# অ্যাডমিন প্যানেল: ব্যান এবং আনব্যান
@bot.message_handler(commands=['ban', 'unban'])
def manage_users(message):
    if message.chat.id == ADMIN_ID:
        try:
            command = message.text.split()[0]
            target_id = int(message.text.split()[1])
            
            if command == '/ban':
                banned_users.add(target_id)
                bot.reply_to(message, f"✅ ইউজার `{target_id}` কে ব্যান করা হয়েছে।", parse_mode='Markdown')
            elif command == '/unban':
                banned_users.discard(target_id)
                bot.reply_to(message, f"✅ ইউজার `{target_id}` এর ব্যান তুলে নেওয়া হয়েছে।", parse_mode='Markdown')
        except:
            bot.reply_to(message, "⚠️ সঠিক নিয়ম: `/ban ইউজার_আইডি` অথবা `/unban ইউজার_আইডি`", parse_mode='Markdown')

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    user_id = message.chat.id
    
    # ব্যান বা লিমিট চেক
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    unique_users.add(user_id)
    input_file = f"{user_id}.mp4"
    output_file = f"{user_id}.3gp"
    
    status_msg = bot.reply_to(message, "⏳ *ভিডিও ডাউনলোড হচ্ছে...*", parse_mode='Markdown')
    
    try:
        bot.send_chat_action(user_id, 'upload_video')
        
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("🔄 *3GP তে কনভার্ট করা হচ্ছে...*\n_দয়া করে অপেক্ষা করুন।_", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        
        command = [
            "ffmpeg", "-y", 
            "-i", input_file, 
            "-c:v", "mpeg4", 
            "-c:a", "aac", 
            "-s", "352x288", 
            "-b:v", "400k", 
            "-b:a", "64k", 
            "-ar", "8000", 
            "-ac", "1", 
            output_file
        ]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            bot.edit_message_text("❌ *কনভার্ট করতে সমস্যা হয়েছে!*", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
            if user_id != ADMIN_ID:
                bot.send_message(ADMIN_ID, f"⚠️ *Error by {user_id}:*\n`{result.stderr[-200:]}`", parse_mode='Markdown')
            return
            
        bot.edit_message_text("✅ *কনভার্ট সফল! আপলোড করা হচ্ছে...*", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        bot.send_chat_action(user_id, 'upload_video')
        
        original_size = os.path.getsize(input_file) / (1024 * 1024)
        new_size = os.path.getsize(output_file) / (1024 * 1024)
        
        # ইউজারের কনভার্ট সংখ্যা আপডেট করা
        user_usage[user_id] = user_usage.get(user_id, 0) + 1
        rem_limit = MAX_LIMIT - user_usage[user_id]
        
        caption = f"🎬 *Converted Successfully!*\n\n📉 Size reduced: {original_size:.1f}MB ➡️ {new_size:.1f}MB"
        if user_id != ADMIN_ID:
            caption += f"\n\n📊 বাকি লিমিট: {rem_limit} টি ভিডিও"
        
        with open(output_file, 'rb') as video:
            bot.send_video(user_id, video, caption=caption, parse_mode='Markdown')
            
        bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text("❌ *দুঃখিত, একটি অনাকাঙ্ক্ষিত সমস্যা হয়েছে।*", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"⚠️ *System Error:*\n`{e}`", parse_mode='Markdown')
    
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

bot.polling(none_stop=True)
