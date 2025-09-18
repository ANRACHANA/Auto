import os
import re
import time
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask
from telethon import TelegramClient, events, Button

# ---------------------- CONFIG ----------------------
API_ID = int(os.getenv("API_ID", "28013497"))
API_HASH = os.getenv("API_HASH", "3bd0587beedb80c8336bdea42fc67e27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7743936268:AAF7thUNZlCx5nSZnvdXG3t2XF2BbcYpEw8")

FACEBOOK_URL = "https://www.facebook.com/share/1FaBZ3ZCWW/?mibextid=wwXIfr"
CONTACT_URL = "https://t.me/vanna_sovanna"

RESTART_DELAY = 5
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
BAD_WORDS = [
    "ref_", "startapp=", "promo code", "gift battle", "win iphone", "t.me/",
    "airdrop", "token", "foxy", "don’t miss", "loyal"
]

def start_bot():
    bot = TelegramClient('bot_session', API_ID,
                         API_HASH).start(bot_token=BOT_TOKEN)

    async def is_admin_or_owner(chat_id, user_id):
        try:
            perms = await bot.get_permissions(chat_id, user_id)
            return perms.is_admin or perms.is_creator
        except:
            return False

    @bot.on(events.NewMessage(pattern=".*"))
    async def handler(event):
        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.chat_id

        # 🛑 Skip messages from bot itself or other bots
        if event.out or sender.bot:
            return

        # 🛑 Skip Admins/Owners
        if await is_admin_or_owner(chat_id, sender_id):
            return

        text = event.raw_text.lower()

        # ------------------ DELETE SPAM/REF + BAN ------------------
        if any(bad in text for bad in BAD_WORDS):
            try:
                await event.delete()
                await bot.edit_permissions(chat_id, sender_id, view_messages=False)  # Ban
                print(f"[{datetime.now()}] ❌ Deleted & banned spammer: {sender_id}")
            except Exception as e:
                print(f"[{datetime.now()}] Failed to delete/ban spammer: {e}")
            return

        # ------------------ DELETE LINKS + BAN ------------------
        if URL_PATTERN.search(event.raw_text):
            try:
                await event.delete()
                await bot.edit_permissions(chat_id, sender_id, view_messages=False)  # Ban
                print(f"[{datetime.now()}] ❌ Deleted & banned link sender: {sender_id}")
            except Exception as e:
                print(f"[{datetime.now()}] Failed to delete/ban link sender: {e}")
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
            buttons=[[
                Button.url("📘 Facebook Page", FACEBOOK_URL),
                Button.url("📞 Admin", CONTACT_URL)
            ]]
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

