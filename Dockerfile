FROM python:3.10-slim

# সার্ভারে ffmpeg ইনস্টল করার কঠোর নির্দেশ
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

# রিকোয়ারমেন্টস কপি করে ইনস্টল করা
COPY requirements.txt .
RUN pip install -r requirements.txt

# বটের কোড কপি করা
COPY . .

# বট চালু করা
CMD ["python", "bot.py"]
