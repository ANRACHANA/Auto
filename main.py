import os
import time
import threading
import requests
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

def ping_self(url):
    while True:
        try:
            requests.get(url)
            print(f"Pinged {url}")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(300)  # Ping every 5 minutes

# Read env vars
API_ID = int(os.getenv("API_ID", "28013497"))
API_HASH = os.getenv("API_HASH", "3bd0587beedb80c8336bdea42fc67e27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk")
APP_URL = os.getenv("APP_URL", "https://auto-4-glod.onrender.com")  # https://your-render-url.onrender.com

if not all([API_ID, API_HASH, BOT_TOKEN, APP_URL]):
    print("Error: Missing one or more environment variables: API_ID, API_HASH, BOT_TOKEN, APP_URL")
    exit(1)

keep_alive()

# Start ping_self thread to keep app alive
threading.Thread(target=ping_self, args=(APP_URL,), daemon=True).start()

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="(?i).*"))
async def handler(event):
    try:
        await event.reply("សួស្តី 😄 ខ្ញុំនឹងឆ្លើយតបឆាប់ៗនេះ សូមអរគុណ!")
    except Exception as e:
        print(f"Error replying to user {event.sender_id}: {e}")

print("Bot started and web server is running...")

bot.run_until_disconnected()
