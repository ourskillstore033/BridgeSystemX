# =========================================================
# TELEGRAM ANONYMOUS GROUP BRIDGE
# RENDER WEB SERVICE VERSION
# =========================================================

import os
import re
import random
from threading import Thread

from flask import Flask
from telethon import TelegramClient, events

# =========================================================
# ENV VARIABLES
# =========================================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GROUP_A_ID = int(os.getenv("GROUP_A_ID"))
GROUP_B_ID = int(os.getenv("GROUP_B_ID"))

# =========================================================
# TELEGRAM CLIENT
# =========================================================

client = TelegramClient(
    "bridge_session",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Anonymous Bridge Bot Running"

# =========================================================
# RANDOM ANON USER IDS
# =========================================================

anonymous_users = {}

def get_anon_name(user_id):

    if user_id not in anonymous_users:
        anonymous_users[user_id] = (
            f"User-{random.randint(1000,9999)}"
        )

    return anonymous_users[user_id]

# =========================================================
# SANITIZE TEXT
# =========================================================

def sanitize_text(text):

    if not text:
        return ""

    # Remove usernames
    text = re.sub(
        r'@\w+',
        '[username removed]',
        text
    )

    # Remove Telegram links
    text = re.sub(
        r'(https?://)?(www\.)?(t\.me|telegram\.me)/\S+',
        '[telegram link removed]',
        text,
        flags=re.IGNORECASE
    )

    # Remove phone numbers
    text = re.sub(
        r'(\+?\d[\d\-\s]{7,}\d)',
        '[number removed]',
        text
    )

    # Remove emails
    text = re.sub(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        '[email removed]',
        text
    )

    return text

# =========================================================
# RELAY FUNCTION
# =========================================================

async def relay_message(event, target_group):

    try:

        sender = await event.get_sender()

        anon_name = get_anon_name(sender.id)

        # Block forwarded messages
        if event.message.fwd_from:
            return

        text = event.raw_text or ""

        clean_text = sanitize_text(text)

        final_caption = (
            f"{anon_name}:\n\n"
            f"{clean_text}"
        )

        # =================================================
        # MEDIA MESSAGES
        # =================================================

        if event.message.media:

            await client.send_file(
                target_group,
                file=event.message.media,
                caption=final_caption
            )

        # =================================================
        # TEXT MESSAGES
        # =================================================

        else:

            await client.send_message(
                target_group,
                final_caption
            )

    except Exception as e:

        print("Relay Error:", e)

# =========================================================
# GROUP A -> GROUP B
# =========================================================

@client.on(events.NewMessage(chats=GROUP_A_ID))
async def group_a_handler(event):

    if event.out:
        return

    await relay_message(event, GROUP_B_ID)

# =========================================================
# GROUP B -> GROUP A
# =========================================================

@client.on(events.NewMessage(chats=GROUP_B_ID))
async def group_b_handler(event):

    if event.out:
        return

    await relay_message(event, GROUP_A_ID)

# =========================================================
# START TELEGRAM BOT
# =========================================================

def run_telegram():

    print("================================")
    print(" ANONYMOUS BRIDGE IS RUNNING ")
    print("================================")

    client.run_until_disconnected()

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    telegram_thread = Thread(target=run_telegram)

    telegram_thread.start()

    PORT = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=PORT
    )
