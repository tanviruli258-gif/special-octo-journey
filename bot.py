import telebot
import os
import subprocess

# আপনার দেওয়া বটের টোকেনটি এখানে বসানো হয়েছে
BOT_TOKEN = "8548108469:AAFmnValzLDBJEiLOfLefWmjknVQ5swuuGI"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগতম! আমাকে যেকোনো MP4 ভিডিও দিন, আমি সেটি 3GP করে দেব। (সর্বোচ্চ সাইজ: 20MB)")

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    try:
        bot.reply_to(message, "ভিডিও ডাউনলোড হচ্ছে... দয়া করে অপেক্ষা করুন।")
        
        # ভিডিও ইনফো নেওয়া
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_file = f"{message.chat.id}.mp4"
        output_file = f"{message.chat.id}.3gp"
        
        # ভিডিও সেভ করা
        with open(input_file, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.send_message(message.chat.id, "ডাউনলোড শেষ! এখন 3GP তে কনভার্ট করা হচ্ছে...")
        
        # FFmpeg দিয়ে কনভার্ট করা (ভিডিও কোয়ালিটি ও সাইজ 3gp অনুযায়ী সেট করা)
        command = f"ffmpeg -y -i {input_file} -s 352x288 -b:v 400k -b:a 64k -ar 8000 -ac 1 {output_file}"
        subprocess.run(command, shell=True)
        
        # কনভার্ট করা ভিডিও পাঠানো
        bot.send_message(message.chat.id, "কনভার্ট সফল! ভিডিওটি আপলোড করা হচ্ছে...")
        with open(output_file, 'rb') as video:
            bot.send_video(message.chat.id, video)
            
    except Exception as e:
        bot.send_message(message.chat.id, "দুঃখিত, কোনো একটি সমস্যা হয়েছে বা ভিডিও সাইজ অনেক বড়। (টেলিগ্রাম বটের ফ্রি লিমিট 20MB)")
    
    finally:
        # সার্ভার থেকে ফাইলগুলো মুছে ফেলা (যাতে স্টোরেজ ফুল না হয়)
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

bot.polling(none_stop=True)
