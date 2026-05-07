import os
import re
import random
import asyncio

from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# =====================================================
# CONFIG
# =====================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

GROUP_A_ID = int(os.environ["GROUP_A_ID"])
GROUP_B_ID = int(os.environ["GROUP_B_ID"])

# =====================================================
# FLASK
# =====================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bridge Running"

# =====================================================
# TELEGRAM CLIENT
# =====================================================

client = TelegramClient(
    "bridge_bot",
    API_ID,
    API_HASH
)

# =====================================================
# RANDOM USER IDs
# =====================================================

users = {}

def anon(uid):

    if uid not in users:
        users[uid] = f"User-{random.randint(1000,9999)}"

    return users[uid]

# =====================================================
# SANITIZE
# =====================================================

def clean(text):

    if not text:
        return ""

    text = re.sub(r'@\w+', '[username removed]', text)

    text = re.sub(
        r'(https?://)?t\.me/\S+',
        '[link removed]',
        text
    )

    text = re.sub(
        r'\+?\d[\d\s\-]{7,}\d',
        '[number removed]',
        text
    )

    return text

# =====================================================
# RELAY FUNCTION
# =====================================================

async def relay(event, target):

    try:

        print("MESSAGE RECEIVED")
        print("CHAT:", event.chat_id)

        # ignore forwarded
        if event.fwd_from:
            return

        sender = await event.get_sender()

        name = anon(sender.id)

        text = clean(event.raw_text or "")

        final = f"{name}:\n\n{text}"

        # media
        if event.media:

            await client.send_file(
                target,
                file=event.media,
                caption=final
            )

        # text
        else:

            await client.send_message(
                target,
                final
            )

        print("FORWARDED SUCCESSFULLY")

    except Exception as e:

        print("ERROR:", e)

# =====================================================
# ALL MESSAGE DETECTOR
# =====================================================

@client.on(events.NewMessage)
async def handler(event):

    try:

        chat = event.chat_id

        # GROUP A -> B
        if chat == GROUP_A_ID:

            await relay(event, GROUP_B_ID)

        # GROUP B -> A
        elif chat == GROUP_B_ID:

            await relay(event, GROUP_A_ID)

    except Exception as e:

        print("HANDLER ERROR:", e)

# =====================================================
# TELEGRAM START
# =====================================================

async def telegram_main():

    await client.start(bot_token=BOT_TOKEN)

    print("================================")
    print(" BRIDGE BOT RUNNING ")
    print("================================")

    await client.run_until_disconnected()

# =====================================================
# RUN FLASK
# =====================================================

def run_flask():

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    flask_thread = Thread(target=run_flask)

    flask_thread.start()

    asyncio.run(telegram_main())
