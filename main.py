import os
import re
import time
import asyncio
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask
from telethon import TelegramClient, events, Button, types

# ---------------------- CONFIG ----------------------
API_ID = int(os.getenv("API_ID", "28013497"))
API_HASH = os.getenv("API_HASH", "3bd0587beedb80c8336bdea42fc67e27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk")

FACEBOOK_URL = "https://www.facebook.com/share/1FaBZ3ZCWW/?mibextid=wwXIfr"
CONTACT_URL = "https://t.me/vanna_sovanna"

RESTART_DELAY = 5
VERIFY_TIMEOUT = 300  # seconds for captcha verification
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

# Memory dicts
last_reply = {}
warn_count = {}
NEW_MEMBERS = {}  # user_id -> (chat_id, join_time)

# Regex Spam Pattern
SPAM_REGEX = re.compile(
    r"(ref_|startapp=|promo\s?code|gift\s?battle|win\s?iphone|#\w+|t\.me/)",
    re.IGNORECASE
)

# Whitelisted domains (allowed links)
WHITELIST = ["t.me/yourchannel", "t.me/yourgroup"]

def start_bot():
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    async def get_group_admins(chat_id):
        """Return list of user IDs who are admin or owner in the group"""
        admins = []
        try:
            async for user in bot.iter_participants(chat_id, filter=types.ChannelParticipantsAdmins):
                admins.append(user.id)
        except Exception as e:
            print(f"Error fetching admins: {e}")
        return admins

    def log_spam(user, text):
        with open("spam.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {user}: {text}\n")

    # ------------------ CAPTCHA / Verification ------------------
    @bot.on(events.ChatAction)
    async def new_member(event):
        if event.user_joined or event.user_added:
            user = await event.get_user()
            chat_id = event.chat_id
            user_id = user.id

            # Restrict new member
            await bot.edit_permissions(chat_id, user_id, send_messages=False)

            NEW_MEMBERS[user_id] = (chat_id, datetime.now())

            await bot.send_message(
                chat_id,
                f"សួស្តី {user.first_name}! សូមចុច ✅ ដើម្បី verify ថាអ្នកមិនមែន spam bot។",
                buttons=[[Button.inline("✅ I’m human", data=f"verify_{user_id}")]]
            )

    @bot.on(events.CallbackQuery(pattern=r"verify_(\d+)"))
    async def verify_user(event):
        user_id = int(event.pattern_match.group(1))
        chat_id = event.chat_id
        sender_id = event.sender_id

        if sender_id != user_id:
            await event.answer("❌ អ្នកមិនមែនអ្នកដែលត្រូវ verify!", alert=True)
            return

        await bot.edit_permissions(chat_id, user_id, send_messages=True)
        await event.edit(f"✅ Verification success! អរគុណ {event.sender.first_name}!")

        if user_id in NEW_MEMBERS:
            del NEW_MEMBERS[user_id]

    async def captcha_watchdog():
        while True:
            now = datetime.now()
            to_kick = []
            for user_id, (chat_id, join_time) in NEW_MEMBERS.items():
                if (now - join_time).total_seconds() > VERIFY_TIMEOUT:
                    to_kick.append((user_id, chat_id))
            for user_id, chat_id in to_kick:
                try:
                    await bot.kick_participant(chat_id, user_id)
                    print(f"Kicked unverified user: {user_id}")
                    del NEW_MEMBERS[user_id]
                except:
                    pass
            await asyncio.sleep(10)

    # ------------------ MAIN MESSAGE HANDLER ------------------
    @bot.on(events.NewMessage(pattern="(?i).*"))
    async def handler(event):
        if event.out:
            return

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.chat_id
        text = event.raw_text or ""

        # Get current admins in group
        admins = await get_group_admins(chat_id)

        # Skip Admin/Owner
        if sender_id in admins:
            print(f"Skipped reply for Admin/Owner: {sender_id}")
            return

        # Whitelist links
        if any(white in text for white in WHITELIST):
            return

        # ------------------ Spam Detection & Auto Delete ------------------
        if SPAM_REGEX.search(text):
            try:
                await event.delete()
                print(f"Deleted spam message from {sender_id}")
            except Exception as e:
                print(f"Failed to delete message: {e}")

            warn_count[sender_id] = warn_count.get(sender_id, 0) + 1
            count = warn_count[sender_id]

            log_spam(sender.username or sender_id, text)

            # PM notify all admins dynamically
            for admin_id in admins:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Spam detected\nUser: {sender_id} (@{sender.username})\nWarn: {count}\nText: {text}"
                    )
                except:
                    pass

            if count == 1:
                await event.respond(f"⚠️ Warning to <a href='tg://user?id={sender_id}'>user</a>: Spam not allowed!",
                                    parse_mode="html")
            elif count == 2:
                try:
                    await bot.kick_participant(chat_id, sender_id)
                    await event.respond(f"🚫 User kicked: @{sender.username or sender_id}")
                except:
                    pass
            elif count >= 3:
                try:
                    await bot.edit_permissions(chat_id, sender_id, view_messages=False)
                    await event.respond(f"⛔ User banned: @{sender.username or sender_id}")
                except:
                    pass
            return

        # Auto reply once/day
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
    asyncio.get_event_loop().create_task(captcha_watchdog())
    bot.run_until_disconnected()

# Watchdog loop
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
