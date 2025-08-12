import os
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

# Read env variables for Telegram API
API_ID = int(os.getenv("API_ID", "28013497"))
API_HASH = os.getenv("API_HASH", "3bd0587beedb80c8336bdea42fc67e27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk")

keep_alive()

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="(?i).*"))
async def handler(event):
    await event.reply("សួស្តី យើងខ្ញុំនិងឆ្លើយតបឆាប់ៗនេះ សូមអរគុណ! ។")

print("Bot started and web server is running...")

bot.run_until_disconnected()
