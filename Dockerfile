FROM python:3.11-slim

# ffmpeg ইনস্টল (native binary — fast conversion)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# টাইমআউট বাড়ানো হলো, বড় ভিডিও কনভার্সনের জন্য
CMD gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:${PORT} app:app --timeout 600
