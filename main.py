import os
import time
from threading import Thread
from datetime import datetime
from flask import Flask
from telethon import TelegramClient, events, Button

# ---------------------- CONFIG ----------------------
API_ID = int(os.getenv("API_ID", "28013497"))
API_HASH = os.getenv("API_HASH", "3bd0587beedb80c8336bdea42fc67e27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk")

OWNER_USERNAME = ""          # username របស់ Owner (គ្មាន @)
ADMIN_USERNAMES = ["", ""]    # username របស់ Admin (គ្មាន @)

FACEBOOK_URL = "https://facebook.com/YOUR_PAGE"
CONTACT_URL = "https://t.me/YOUR_USERNAME"

RESTART_DELAY = 5  # វិនាទីចាំមុន restart
# ----------------------------------------------------

# Flask keep-alive
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# Telegram bot logic
def start_bot():
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    @bot.on(events.NewMessage(pattern="(?i).*"))
    async def handler(event):
        sender = await event.get_sender()
        sender_username = (sender.username or "").lower()

        # មិនឆ្លើយ Owner/Admin
        if sender_username == OWNER_USERNAME.lower() or sender_username in [u.lower() for u in ADMIN_USERNAMES]:
            return

        if event.is_private and not event.out:
            await event.reply(
                "សួស្តី! ជ្រើសរើសប៊ូតុងខាងក្រោម៖",
                buttons=[
                    [
                        Button.url("📘 Facebook", FACEBOOK_URL),
                        Button.url("📞 Contact", CONTACT_URL)
                    ]
                ]
            )

    print(f"[{datetime.now()}] Bot started and running...")
    bot.run_until_disconnected()

# Watchdog internal loop
def run_with_watchdog():
    keep_alive()
    while True:
        try:
            start_bot()
        except Exception as e:
            print(f"[{datetime.now()}] [ERROR] {e}")
            print(f"[{datetime.now()}] Restarting bot in {RESTART_DELAY} seconds...")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    run_with_watchdog()
