import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import subprocess
from datetime import datetime, timedelta

# আপনার টোকেন
BOT_TOKEN = "7685589352:AAEfJKL8kOKemZ5wTAnHhUwMeX6i3sz0ujc"
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার টেলিগ্রাম User ID
ADMIN_ID = 6468726869  

unique_users = set()
banned_users = set()

# ইউজারদের ডাটা সেভ রাখার ডিকশনারি
user_usage = {}
DEFAULT_LIMIT = 5

# সাময়িকভাবে ভিডিওর ফাইল আইডি সেভ রাখার জন্য
pending_videos = {}

# বাংলাদেশ সময় অনুযায়ী আজকের তারিখ বের করার ফাংশন
def get_bd_date():
    return (datetime.utcnow() + timedelta(hours=6)).date()

# ইউজারের লিমিট এবং ডাটা চেক ও রিসেট করার ফাংশন
def get_user_data(user_id):
    today = get_bd_date()
    
    if user_id not in user_usage:
        user_usage[user_id] = {'date': today, 'count': 0, 'limit': DEFAULT_LIMIT}
    elif user_usage[user_id]['date'] != today:
        # রাত ১২টার পর নতুন তারিখ হলে কাউন্ট জিরো হয়ে যাবে
        user_usage[user_id]['date'] = today
        user_usage[user_id]['count'] = 0
        
    return user_usage[user_id]

def is_allowed(user_id):
    if user_id in banned_users:
        return False, "❌ Banned!"
    
    user_data = get_user_data(user_id)
    if user_data['count'] >= user_data['limit'] and user_id != ADMIN_ID:
        return False, "⚠️ আজকের লিমিট শেষ! রাত ১২টার পর আবার ট্রাই করুন।"
        
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

    bot.reply_to(message, "👋 Welcome!\n\nSend me any *MP4* video (Max 20MB).", parse_mode='Markdown')

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

# ইউজারের লিমিট বাড়ানোর জন্য নতুন অ্যাডমিন কমান্ড
@bot.message_handler(commands=['setlimit'])
def set_limit(message):
    if message.chat.id == ADMIN_ID:
        try:
            _, target_id, new_limit = message.text.split()
            target_id = int(target_id)
            new_limit = int(new_limit)
            
            user_data = get_user_data(target_id)
            user_data['limit'] = new_limit
            bot.reply_to(message, f"✅ User `{target_id}` এর লিমিট বাড়িয়ে {new_limit} করা হয়েছে।", parse_mode='Markdown')
        except:
            bot.reply_to(message, "⚠️ Format: `/setlimit user_id new_limit`\nউদাহরণ: `/setlimit 123456789 20`", parse_mode='Markdown')

# ভিডিও রিসিভ করার ফাংশন
@bot.message_handler(content_types=['video', 'document'])
def handle_direct_video(message):
    user_id = message.chat.id
    
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.reply_to(message, msg)
        return

    unique_users.add(user_id)
    
    file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("convert video", callback_data="do_convert"))
    
    status_msg = bot.reply_to(message, "ভিডিওটি প্রসেস করতে নিচের বাটনে ক্লিক করুন:", reply_markup=markup)
    
    # বাটন মেসেজ আইডির সাথে ভিডিওর ফাইল আইডি সেভ রাখা হলো
    pending_videos[status_msg.message_id] = file_id

# কনভার্ট বাটন ক্লিক করার ফাংশন
@bot.callback_query_handler(func=lambda call: call.data == 'do_convert')
def process_convert(call):
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if msg_id not in pending_videos:
        bot.answer_callback_query(call.id, "❌ ভিডিওটি এক্সপায়ার হয়ে গেছে। আবার সেন্ড করুন।")
        return
        
    # বাটন চাপার পর আবার লিমিট চেক করা (যাতে স্প্যাম না হয়)
    allowed, msg = is_allowed(user_id)
    if not allowed:
        bot.answer_callback_query(call.id, "⚠️ আপনার আজকের লিমিট শেষ!")
        return
        
    file_id = pending_videos.pop(msg_id)
    
    input_file = f"{user_id}.mp4"
    output_file = f"{user_id}.3gp"
    
    bot.edit_message_text("⏳ Downloading...", chat_id=user_id, message_id=msg_id)
    
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("🔄 Converting to 3GP...", chat_id=user_id, message_id=msg_id)
        
        command = ["ffmpeg", "-y", "-i", input_file, "-c:v", "mpeg4", "-c:a", "aac", "-s", "352x288", "-b:v", "400k", "-b:a", "64k", "-ar", "8000", "-ac", "1", output_file]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            bot.edit_message_text(f"❌ Conversion Error:\n`{result.stderr[-100:]}`", chat_id=user_id, message_id=msg_id, parse_mode='Markdown')
            return
            
        bot.edit_message_text("✅ Uploading...", chat_id=user_id, message_id=msg_id)
        
        # সফলভাবে আপলোড হলে কাউন্ট ১ বাড়বে
        user_data = get_user_data(user_id)
        user_data['count'] += 1
        rem = user_data['limit'] - user_data['count']
        
        caption = "🎬 Done!"
        if user_id != ADMIN_ID:
            caption += f"\n📊 Limit left: {rem}"
            
        with open(output_file, 'rb') as video:
            bot.send_video(user_id, video, caption=caption)
            
        bot.delete_message(user_id, msg_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error:\n`{str(e)[:100]}`", chat_id=user_id, message_id=msg_id, parse_mode='Markdown')
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"⚠️ System Error:\n`{e}`", parse_mode='Markdown')
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

bot.polling(none_stop=True)
