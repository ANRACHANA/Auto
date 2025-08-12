from telethon import TelegramClient, events, Button
import os
from langdetect import detect, DetectorFactory
from datetime import datetime, date
import asyncio

DetectorFactory.seed = 0

API_ID = int(os.getenv('API_ID', '28013497'))
API_HASH = os.getenv('API_HASH', '3bd0587beedb80c8336bdea42fc67e27')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7045596311:AAH7tHcSt16thbFpL0JsVNSEHBvKtjnK8sk')

OWNER_USERNAME = 'yourownerusername'  # ប្ដូរតាមអ្នក
ADMIN_LIST = ['adminname2', 'anotheradmin']

REPLIES = {
    'km': "សួស្តី {first} {last} 😊",
    'en': "Hello <b><u><font color='blue'>{first} {last}</font></u></b>\nTime: {time}",
    'default': "Hello {first} {last} 😊",
}

CONTACT_OPTIONS = [
    [Button.inline('💬 Telegram', b'telegram')],
    [Button.inline('💬 WeChat', b'wechat')],
    [Button.inline('📧 Email', b'email')],
    [Button.inline('📞 Phone', b'phone')],
    [Button.inline('🔙 Back', b'back_to_main')]
]

def disabled_contact_options():
    return [
        [Button.inline('💬 Telegram', b'noop', ignored=True)],
        [Button.inline('💬 WeChat', b'noop', ignored=True)],
        [Button.inline('📧 Email', b'noop', ignored=True)],
        [Button.inline('📞 Phone', b'noop', ignored=True)],
        [Button.inline('🔙 Back', b'noop', ignored=True)]
    ]

user_last_reply = {}
last_reply_messages = {}

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def send_main_message(event, sender):
    first_name = sender.first_name if sender else ""
    last_name = sender.last_name if sender else ""
    if last_name is None:
        last_name = ""

    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        lang = detect(event.message.message)
        if lang not in ['km', 'en']:
            lang = 'default'
    except:
        lang = 'default'

    reply_text = REPLIES.get(lang, REPLIES['default']).format(
        first=first_name,
        last=last_name,
        time=now_time
    )

    buttons = [[
        Button.url('🌐 Visit Website', 'https://example.com'),
        Button.inline('📞 Contact Us', b'open_contact')
    ]]

    msg = await event.reply(
        reply_text,
        buttons=buttons,
        parse_mode='html'
    )
    return msg

@bot.on(events.NewMessage(pattern='(?i).*'))
async def handler(event):
    sender = await event.get_sender()
    user_id = sender.id if sender else None
    try:
        username = sender.username.lower() if sender and sender.username else ""
    except:
        username = ""

    if username == OWNER_USERNAME.lower():
        print(f"[LOG] Message ពី owner @{username} មិនឆ្លើយតប។")
        return
    if username in [admin.lower() for admin in ADMIN_LIST]:
        print(f"[LOG] Message ពី admin @{username} មិនឆ្លើយតប។")
        return

    today_str = date.today().isoformat()

    if user_id in user_last_reply and user_last_reply[user_id] == today_str:
        print(f"[LOG] User {user_id} បានឆ្លើយសារមួយរួចហើយថ្ងៃនេះ។ មិនឆ្លើយទៀត។")
        return

    msg = await send_main_message(event, sender)

    user_last_reply[user_id] = today_str
    last_reply_messages[user_id] = msg

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data
    sender = await event.get_sender()
    user_id = sender.id if sender else None

    if data == b'noop':
        await event.answer('', alert=False)
        return

    if data == b'open_contact':
        msg = await event.edit(
            "📞 សូមជ្រើសរើសមធ្យោបាយទំនាក់ទំនង៖",
            buttons=CONTACT_OPTIONS
        )
        await asyncio.sleep(60)
        try:
            await msg.edit("📞 សូមជ្រើសរើសមធ្យោបាយទំនាក់ទំនង៖ (menu closed)", buttons=disabled_contact_options())
        except:
            pass
        await asyncio.sleep(60)
        try:
            await msg.edit("📞 សូមជ្រើសរើសមធ្យោបាយទំនាក់ទំនង៖", buttons=CONTACT_OPTIONS)
        except:
            pass

    elif data == b'back_to_main':
        if user_id in last_reply_messages:
            try:
                await last_reply_messages[user_id].edit(
                    last_reply_messages[user_id].message,
                    buttons=[[
                        Button.url('🌐 Visit Website', 'https://example.com'),
                        Button.inline('📞 Contact Us', b'open_contact')
                    ]],
                    parse_mode='html'
                )
            except:
                await send_main_message(event, sender)
        else:
            await send_main_message(event, sender)

    elif data == b'telegram':
        await event.answer('Telegram: https://t.me/yourtelegramusername', alert=True)

    elif data == b'wechat':
        await event.answer('WeChat ID: yourwechatid', alert=True)

    elif data == b'email':
        await event.answer('Email: youremail@example.com', alert=True)

    elif data == b'phone':
        await event.answer('Phone: +1234567890', alert=True)

print("🤖 Bot is running...")
bot.run_until_disconnected()
