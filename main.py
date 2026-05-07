import os
import re
import random
import asyncio

from flask import Flask
from telethon import TelegramClient, events

# ======================================================
# CONFIG
# ======================================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GROUP_A_ID = int(os.getenv("GROUP_A_ID"))
GROUP_B_ID = int(os.getenv("GROUP_B_ID"))

# ======================================================
# FLASK APP
# ======================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Anonymous Bridge Running"

# ======================================================
# TELEGRAM CLIENT
# ======================================================

client = TelegramClient(
    "bot_session",
    API_ID,
    API_HASH
)

# ======================================================
# USER CACHE
# ======================================================

users = {}

def anon(uid):

    if uid not in users:
        users[uid] = f"User-{random.randint(1000,9999)}"

    return users[uid]

# ======================================================
# SANITIZE
# ======================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(r'@\w+', '[username removed]', text)

    text = re.sub(
        r'(https?://)?t\.me/\S+',
        '[telegram link removed]',
        text
    )

    text = re.sub(
        r'\+?\d[\d\s\-]{7,}\d',
        '[number removed]',
        text
    )

    return text

# ======================================================
# RELAY
# ======================================================

async def relay(event, target):

    try:

        # Block forwarded messages
        if event.message.fwd_from:
            return

        sender = await event.get_sender()

        name = anon(sender.id)

        text = clean_text(event.raw_text or "")

        final = f"{name}:\n\n{text}"

        # MEDIA
        if event.message.media:

            await client.send_file(
                target,
                file=event.message.media,
                caption=final
            )

        # TEXT
        else:

            await client.send_message(
                target,
                final
            )

    except Exception as e:

        print("RELAY ERROR:", e)

# ======================================================
# GROUP A -> GROUP B
# ======================================================

@client.on(events.NewMessage(chats=GROUP_A_ID))
async def group_a(event):

    if event.out:
        return

    await relay(event, GROUP_B_ID)

# ======================================================
# GROUP B -> GROUP A
# ======================================================

@client.on(events.NewMessage(chats=GROUP_B_ID))
async def group_b(event):

    if event.out:
        return

    await relay(event, GROUP_A_ID)

# ======================================================
# MAIN
# ======================================================

async def main():

    await client.start(bot_token=BOT_TOKEN)

    print("================================")
    print(" ANONYMOUS BRIDGE IS RUNNING ")
    print("================================")

    flask_task = asyncio.to_thread(
        app.run,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

    telegram_task = client.run_until_disconnected()

    await asyncio.gather(
        flask_task,
        telegram_task
    )

asyncio.run(main())
