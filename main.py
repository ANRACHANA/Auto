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
RESET_INTERVAL_HOURS = 24  # ✅ Auto clean interval
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

# Global memory
last_reply = {}
reply_count = {}
admin_replied = set()

URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
BAD_WORDS = ["ref_", "startapp=", "promo code", "gift battle", "win iphone", "t.me/"]

# ---------------------- AUTO RESET ----------------------
def auto_reset_data():
    """Automatically reset bot memory every 24h"""
    while True:
        time.sleep(RESET_INTERVAL_HOURS * 3600)
        last_reply.clear()
        reply_count.clear()
        admin_replied.clear()
        print(f"[{datetime.now()}] ✅ Auto data reset completed (24h cleanup)")
# ---------------------------------------------------------

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
            # ✅ Mark that admin replied to this user
            if event.is_reply:
                replied = await event.get_reply_message()
                if replied and replied.sender_id:
                    admin_replied.add(replied.sender_id)
            return

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.chat_id
        text = event.raw_text.strip()

        # Skip admins
        if await is_admin_or_owner(chat_id, sender_id):
            return

        # If admin already replied → stop replying
        if sender_id in admin_replied:
            return

        # Delete spam or links
        if any(bad in text.lower() for bad in BAD_WORDS):
            try:
                await event.delete()
                await bot.kick_participant(chat_id, sender_id)
                print(f"[{datetime.now()}] Deleted & kicked spammer: {sender_id}")
            except Exception as e:
                print(f"Failed to delete/kick spammer: {e}")
            return

        if URL_PATTERN.search(text):
            try:
                await event.delete()
                print(f"[{datetime.now()}] Deleted link message from {sender_id}")
            except:
                pass
            return

        # Handle user messages
        now = datetime.now()
        reply_count[sender_id] = reply_count.get(sender_id, 0) + 1

        sender_username = f"@{sender.username}" if sender.username else ""
        sender_last = sender.last_name or sender.first_name or "អ្នកប្រើប្រាស់"

        # --- Within same day ---
        if sender_id in last_reply and now - last_reply[sender_id] < timedelta(days=1):
            if reply_count[sender_id] == 2:
                await event.reply(
                    f"សូមអធ្យាស្រ័យ {sender_username} {sender_last} 🙏\n\n"
                    f"អ្នកអាចទំនាក់ទំនង Admin ផ្ទាល់សម្រាប់សាកសួរ។\n\n"
                    f"សាររបស់អ្នក៖ “{text}”\n\nសូមអរគុណ 💙",
                    buttons=[
                        [Button.url("📞 ទាក់ទង Admin", CONTACT_URL)],
                        [Button.url("📘 Facebook Page", FACEBOOK_URL)]
                    ]
                )
            return

        # --- First message of the day ---
        last_reply[sender_id] = now
        await event.reply(
            f"សួស្តី! {sender_username} {sender_last} 👋\n"
            f"យើងខ្ញុំនឹងតបសារឆាប់ៗនេះ សូមអធ្យាស្រ័យចំពោះការឆ្លើយយឺត 🙏",
            buttons=[
                [
                    Button.url("📘 Facebook Page", FACEBOOK_URL),
                    Button.url("📞 Admin", CONTACT_URL)
                ]
            ]
        )

    print(f"[{datetime.now()}] Bot started and running...")
    bot.run_until_disconnected()

def run_with_watchdog():
    keep_alive()

    # ✅ Start auto reset thread
    reset_thread = Thread(target=auto_reset_data)
    reset_thread.daemon = True
    reset_thread.start()

    while True:
        try:
            start_bot()
        except Exception as e:
            print(f"[{datetime.now()}] [ERROR] {e}")
            print(f"[{datetime.now()}] Restarting bot in {RESTART_DELAY} seconds...")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    run_with_watchdog()
