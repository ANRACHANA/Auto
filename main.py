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

# Track last bot reply per user
last_reply = {}
# Track if admin replied to user
admin_replied = {}

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

    # Detect when admin replies to a user (so bot stops replying)
    @bot.on(events.NewMessage(outgoing=True))
    async def track_admin_reply(event):
        if event.is_private:
            user_id = event.chat_id
            admin_replied[user_id] = True
            print(f"[{datetime.now()}] Admin replied to {user_id} -> stop auto replies")

    @bot.on(events.NewMessage(pattern=".*"))
    async def handler(event):
        if event.out:
            return  # Ignore bot's own messages

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.chat_id

        # Skip Admins/Owners
        if await is_admin_or_owner(chat_id, sender_id):
            return

        # If admin already replied to this user -> stop replying permanently
        if admin_replied.get(sender_id, False):
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

        # ------------------ AUTO-REPLY LOGIC ------------------
        now = datetime.now()
        last_time = last_reply.get(sender_id, None)
        reply_count = last_reply.get(f"{sender_id}_count", 0)

        sender_username = f"@{sender.username}" if sender.username else ""
        sender_first = sender.first_name or ""
        sender_last = sender.last_name or ""
        display_name = f"{sender_username} {sender_last or sender_first}".strip()

        # Reset count after 1 day
        if last_time and now - last_time >= timedelta(days=1):
            reply_count = 0

        # First auto reply
        if reply_count == 0:
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
            last_reply[sender_id] = now
            last_reply[f"{sender_id}_count"] = 1
            admin_replied[sender_id] = False
            return

        # Second auto reply (if admin hasn't replied yet)
        elif reply_count == 1:
            await event.reply(
                f"សូមអធ្យាស្រ័យ {display_name} ខាងខ្ញុំនឹងតបអ្នកឆាប់ៗនេះ 🙏💙"
            )
            last_reply[sender_id] = now
            last_reply[f"{sender_id}_count"] = 2
            return

        # Otherwise, ignore further messages
        return

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
