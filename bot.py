import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import subprocess

# আপনার টোকেন
BOT_TOKEN = "8548108469:AAFmnValzLDBJEiLOfLefWmjknVQ5swuuGI"
bot = telebot.TeleBot(BOT_TOKEN)

# IMPORTANT: নিচে 123456789 এর জায়গায় আপনার নিজের টেলিগ্রাম User ID বসান
ADMIN_ID = 7392861032  

# ডাটাবেজ ছাড়া বর্তমান ইউজার ট্র্যাক করার জন্য
unique_users = set()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    unique_users.add(user_id)
    
    # নতুন ইউজার আসলে অ্যাডমিনকে নোটিফিকেশন পাঠানো
    if user_id != ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID, f"🔔 *নতুন ইউজার!*\nনাম: {message.from_user.first_name}\nআইডি: `{user_id}`", parse_mode='Markdown')
        except:
            pass

    # সুন্দর একটি বাটন তৈরি
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🧑‍💻 Developer", url="https://t.me/your_telegram_username")) # এখানে আপনার ইউজারনেম দিতে পারেন
    
    welcome_text = (
        f"স্বাগতম *{message.from_user.first_name}*! 👋\n\n"
        "আমি একটি প্রোফেশনাল ভিডিও কনভার্টার বট। আমাকে যেকোনো *MP4* ভিডিও দিন, "
        "আমি সেটি দ্রুত *3GP* ফরম্যাটে কনভার্ট করে দেব।\n\n"
        "💡 _অপেক্ষাকৃত ছোট সাইজের ভিডিও দিন যাতে দ্রুত কনভার্ট হয়।_"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

# শুধুমাত্র অ্যাডমিনের জন্য সিক্রেট কমান্ড
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, f"📊 *বটের বর্তমান পরিসংখ্যান:*\n\nমোট ইউজার (রিস্টার্টের পর): {len(unique_users)} জন", parse_mode='Markdown')
    else:
        pass # অন্য কেউ এই কমান্ড দিলে বট কোনো রিপ্লাই দেবে না

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    user_id = message.chat.id
    unique_users.add(user_id)
    input_file = f"{user_id}.mp4"
    output_file = f"{user_id}.3gp"
    
    # একটি মাত্র লোডিং মেসেজ দেওয়া হলো (এটিকেই বারবার আপডেট করা হবে)
    status_msg = bot.reply_to(message, "⏳ *ভিডিও ডাউনলোড হচ্ছে...*", parse_mode='Markdown')
    
    try:
        # উপরে "uploading video..." স্ট্যাটাস দেখাবে
        bot.send_chat_action(user_id, 'upload_video')
        
        # ভিডিও ডাউনলোড
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # মেসেজটি এডিট করে নতুন স্ট্যাটাস দেওয়া হলো
        bot.edit_message_text("🔄 *3GP তে কনভার্ট করা হচ্ছে...*\n_দয়া করে অপেক্ষা করুন।_", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        
        # FFmpeg কমান্ড (আগের এনকোডার ফিক্স সহ)
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
                # ইউজারকে না দেখিয়ে আসল এররটি শুধু অ্যাডমিনকে পাঠানো হবে
                bot.send_message(ADMIN_ID, f"⚠️ *Error by {user_id}:*\n`{result.stderr[-200:]}`", parse_mode='Markdown')
            return
            
        bot.edit_message_text("✅ *কনভার্ট সফল! আপলোড করা হচ্ছে...*", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        bot.send_chat_action(user_id, 'upload_video')
        
        # অরিজিনাল এবং নতুন ভিডিওর সাইজ বের করা
        original_size = os.path.getsize(input_file) / (1024 * 1024)
        new_size = os.path.getsize(output_file) / (1024 * 1024)
        
        # ভিডিওর নিচে প্রোফেশনাল ক্যাপশন
        caption = f"🎬 *Converted Successfully!*\n\n📉 Size reduced: {original_size:.1f}MB ➡️ {new_size:.1f}MB"
        
        with open(output_file, 'rb') as video:
            bot.send_video(user_id, video, caption=caption, parse_mode='Markdown')
            
        # কাজ শেষ! এবার সেই বিরক্তিকর লোডিং মেসেজটি ডিলিট করে দেওয়া হলো
        bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text("❌ *দুঃখিত, একটি অনাকাঙ্ক্ষিত সমস্যা হয়েছে।*", chat_id=user_id, message_id=status_msg.message_id, parse_mode='Markdown')
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"⚠️ *System Error:*\n`{e}`", parse_mode='Markdown')
    
    finally:
        # স্টোরেজ ক্লিয়ার করা
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

bot.polling(none_stop=True)
