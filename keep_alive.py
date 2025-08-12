from telethon import TelegramClient, events
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

API_ID = int(os.getenv('API_ID', '28013497'))          # ឬបញ្ចូលលេខអ្នកផ្ទាល់
API_HASH = os.getenv('API_HASH', '3bd0587beedb80c8336bdea42fc67e27')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk')

keep_alive()

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='(?i).*'))
async def handler(event):
    await event.reply("Hello! Bot is alive.")

print("🤖 Bot is running...")

bot.run_until_disconnected()
