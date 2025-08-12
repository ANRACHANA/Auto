import os
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from langdetect import detect, DetectorFactory
from datetime import datetime

DetectorFactory.seed = 0

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

# Telegram API Credentials from environment variables
API_ID = int(os.getenv('API_ID', '28013497'))
API_HASH = os.getenv('API_HASH', '3bd0587beedb80c8336bdea42fc67e27')
BOT_TOKEN = os.getenv('BOT_TOKEN','7779226082:AAGfoJvuy86HVMzhc6cZQa0lrzs9Zw6lZb8')

OWNER_USERNAME = ''
ADMIN_LIST = ['adminname2', 'anotheradmin']

REPLIES = {
    'km':
    "សួស្តី {first} {last} !​យើងខ្ញុំនិងតបសារឆាប់ៗនេះ សូមអធ្យាស្រ័យចំពោះការឆ្លើយតបយឺតយ៉ាវ។ សូមអរគុណ 💙🙏",
    'en':
    "Hello <b><u><font color='blue'>{first} {last}</font></u></b>\nTime: {time}",
    'default':
    "សួស្តី  @{first}{last}​យើងខ្ញុំនិងតបសារឆាប់ៗនេះ សូមអធ្យាស្រ័យចំពោះការឆ្លើយតបយឺតយ៉ាវ ។ I will reply shortly. Sorry for the delayed response. Thank you 💙🙏😊",
}

keep_alive()

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='(?i).*'))
async def handler(event):
    sender = await event.get_sender()
    try:
        username = sender.username.lower() if sender and sender.username else ""
    except:
        username = ""

    # មិនឆ្លើយតបទៅ owner និង admin
    if username == OWNER_USERNAME.lower():
        print(f"[LOG] Message ពី owner @{username} មិនឆ្លើយតប។")
        return
    if username in [admin.lower() for admin in ADMIN_LIST]:
        print(f"[LOG] Message ពី admin @{username} មិនឆ្លើយតប។")
        return

    incoming_text = event.message.message

    first_name = sender.first_name if sender else ""
    last_name = sender.last_name if sender else ""
    if last_name is None:
        last_name = ""

    try:
        lang = detect(incoming_text)
        if lang not in ['km', 'en']:
            lang = 'default'
    except:
        lang = 'default'

    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    reply_text = REPLIES.get(lang, REPLIES['default']).format(
        first=first_name,
        last=last_name,
        time=now_time
    )

    await event.reply(reply_text,
          buttons=[[
              Button.url('🌐  Facebook Page', 'https://www.facebook.com/share/1FaBZ3ZCWW/?mibextid=wwXIfr'),
              Button.url('📞 Telegram Admin',
                         'https://t.me/vanna_sovanna')
          ]],
          parse_mode='html')

print("🤖 Bot is running...")

bot.run_until_disconnected()
