import os
import re
import time
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask
from telethon import TelegramClient, events, Button

# ---------------------- CONFIG ----------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

FACEBOOK_URL = os.getenv("FACEBOOK_URL", "https://www.facebook.com/")
CONTACT_URL = os.getenv("CONTACT_URL", "https://t.me/")

RESTART_DELAY = int(os.getenv("RESTART_DELAY", 5))
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

# Dictionary to track last reply time per user
last_reply = {}

# Regex to detect URLs
URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)

# Spam/ref keywords
BAD_WORDS = ["ref_", "startapp=", "promo code", "gift battle", "win iphone", "t.me/"]

def start_bot():
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    async def is_admin_or_owner(chat_id, user_id):
        try:
            perms = await bot.get_permissions(chat_id, user_id)
            return perms.is_admin or perms.is_creator
        except:
            return False

    @bot.on(events.NewMessage(pattern=".*"))
    async def handler(event):
        if event.out:
            return  # Ignore messages sent by the bot itself

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.chat_id

        # Skip Admins/Owners
        if await is_admin_or_owner(chat_id, sender_id):
            return

        text = event.raw_text.lower()

        # ------------------ DELETE SPAM/REF ------------------
        if any(bad in text for bad in BAD_WORDS):
            try:
                await event.delete()
                await bot.kick_participant(chat_id, sender_id)
                print(f"[{datetime.now()}] Deleted & kicked spammer: {sender_id}")
            except Exception as e:
                print(f"[{datetime.now()}] Failed to delete/kick spammer: {e}")
            return

        # ------------------ DELETE LINKS ------------------
        if URL_PATTERN.search(event.raw_text):
            try:
                await event.delete()
                print(f"[{datetime.now()}] Deleted message with link from {sender_id}")
            except Exception as e:
                print(f"[{datetime.now()}] Failed to delete message with link: {e}")
            return

        # ------------------ AUTO-REPLY ONCE PER DAY ------------------
        now = datetime.now()
        if sender_id in last_reply and now - last_reply[sender_id] < timedelta(days=1):
            return
        last_reply[sender_id] = now

        sender_username = sender.username
        sender_first = sender.first_name or ""
        sender_last = sender.last_name or ""
        if sender_username:
            display_name = f"@{sender_username} {sender_last}"
        else:
            display_name = sender_last if sender_last else sender_first

        await event.reply(
            f"សួស្តី! {display_name} យើងខ្ញុំនឹងតបសារឆាប់ៗនេះ "
            f"សូមអធ្យាស្រ័យចំពោះការឆ្លើយយឺត។ I will reply shortly. Thank you 💙🙏",
            buttons=[
                [
                    Button.url("📘 Facebook Page", FACEBOOK_URL),
                    Button.url("📞 Admin", CONTACT_URL)
                ]
            ]
        )

    print(f"[{datetime.now()}] Bot started and running...")
    bot.run_until_disconnected()

# Watchdog loop to auto-restart bot on errors
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
