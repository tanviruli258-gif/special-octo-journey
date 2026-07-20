import telebot
import os
import subprocess

# আপনার টোকেন
BOT_TOKEN = "8548108469:AAFmnValzLDBJEiLOfLefWmjknVQ5swuuGI"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগতম! আমাকে যেকোনো MP4 ভিডিও দিন, আমি সেটি 3GP করে দেব।")

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    input_file = f"{message.chat.id}.mp4"
    output_file = f"{message.chat.id}.3gp"
    
    try:
        bot.reply_to(message, "ভিডিও ডাউনলোড হচ্ছে... দয়া করে অপেক্ষা করুন।")
        
        # ভিডিও ইনফো নেওয়া
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ভিডিও সেভ করা
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.send_message(message.chat.id, "ডাউনলোড শেষ! এখন 3GP তে কনভার্ট করা হচ্ছে...")
        
        # FFmpeg কমান্ড (এখানে এনকোডার ফিক্স করা হয়েছে: -c:v mpeg4 এবং -c:a aac)
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
        
        # কমান্ড রান করা 
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # যদি কনভার্ট ফেইল করে
        if result.returncode != 0:
            bot.send_message(message.chat.id, f"FFmpeg Error:\n{result.stderr[-200:]}")
            return
            
        # কনভার্ট সফল হলে ভিডিও পাঠানো
        bot.send_message(message.chat.id, "কনভার্ট সফল! ভিডিওটি আপলোড করা হচ্ছে...")
        with open(output_file, 'rb') as video:
            bot.send_video(message.chat.id, video)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"দুঃখিত, একটি সমস্যা হয়েছে: {e}")
    
    finally:
        # স্টোরেজ ক্লিয়ার করা
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

bot.polling(none_stop=True)
