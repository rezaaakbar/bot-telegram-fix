import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

================= CONFIG =================

TOKEN = "7506774072:AAF0f7FYsk0i7J_cElq-RjoBTEv7Jw7okhE"
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

================= DATABASE =================

data = {"groups": {}}
user_group_map = {}

def load_data():
global data, user_group_map
if os.path.exists("database.json"):
with open("database.json", "r") as f:
db = json.load(f)
data = db.get("data", {"groups": {}})
user_group_map = db.get("user_group_map", {})
else:
data = {"groups": {}}
user_group_map = {}

def save_data():
with open("database.json", "w") as f:
json.dump({
"data": data,
"user_group_map": user_group_map
}, f)

def get_group(chat_id):
chat_id = str(chat_id)
if chat_id not in data["groups"]:
data["groups"][chat_id] = {
"targets": [],
"enabled": False,
"users": []
}
return data["groups"][chat_id]

def is_owner(user_id):
return user_id == OWNER_ID

def is_user(user_id, chat_id, group):
return user_id in group["users"] and user_group_map.get(str(user_id)) == str(chat_id)

================= COMMAND =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
chat_id = update.effective_chat.id
group = get_group(chat_id)

if not (is_owner(user_id) or is_user(user_id, chat_id, group)):  
    await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")  
    return  

if not context.args:  
    return  

try:  
    member = await context.bot.get_chat_member(chat_id, context.args[0])  
    target_id = member.user.id  

    if target_id == OWNER_ID:  
        await update.message.reply_text("TIDAK BISA TARGET OWNER ❌")  
        return  

    if target_id in group["users"]:  
        await update.message.reply_text("TIDAK BISA TARGET SESAMA USER ❌")  
        return  

    if target_id not in group["targets"]:  
        group["targets"].append(target_id)  
        save_data()  

    await update.message.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")  
except:  
    await update.message.reply_text("User tidak ditemukan di grup")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
chat_id = update.effective_chat.id
group = get_group(chat_id)

if not (is_owner(user_id) or is_user(user_id, chat_id, group)):  
    await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")  
    return  

if not context.args:  
    return  

try:  
    member = await context.bot.get_chat_member(chat_id, context.args[0])  
    target_id = member.user.id  

    if target_id in group["targets"]:  
        group["targets"].remove(target_id)  
        save_data()  

    await update.message.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")  
except:  
    await update.message.reply_text("User tidak ditemukan")

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
chat_id = update.effective_chat.id
group = get_group(chat_id)

if not group["targets"]:  
    await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")  
    return  

text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"  
for i, uid in enumerate(group["targets"], 1):  
    text += f"{i}. {uid}\n"  

await update.message.reply_text(text)

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
chat_id = update.effective_chat.id
group = get_group(chat_id)

if not (is_owner(user_id) or is_user(user_id, chat_id, group)):  
    await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")  
    return  

if not context.args:  
    return  

mode = context.args[0].lower()  

if mode == "on":  
    group["enabled"] = True  
    save_data()  
    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦𝗦𝗦🚀")  
elif mode == "off":  
    group["enabled"] = False  
    save_data()  
    await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

================= OWNER ONLY =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if not is_owner(user_id):
await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
return

chat_id = update.effective_chat.id  
group = get_group(chat_id)  

try:  
    member = await context.bot.get_chat_member(chat_id, context.args[0])  
    target_id = member.user.id  

    if str(target_id) in user_group_map and user_group_map[str(target_id)] != str(chat_id):  
        await update.message.reply_text("USER SUDAH TERDAFTAR DI GRUP LAIN ❌")  
        return  

    if target_id not in group["users"]:  
        group["users"].append(target_id)  
        user_group_map[str(target_id)] = str(chat_id)  
        save_data()  

    await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")  
except:  
    await update.message.reply_text("User tidak ditemukan")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if not is_owner(user_id):
await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
return

chat_id = update.effective_chat.id  
group = get_group(chat_id)  

try:  
    member = await context.bot.get_chat_member(chat_id, context.args[0])  
    target_id = member.user.id  

    if target_id in group["users"]:  
        group["users"].remove(target_id)  
        user_group_map.pop(str(target_id), None)  
        save_data()  

    await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")  
except:  
    await update.message.reply_text("User tidak ditemukan")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if not is_owner(user_id):
await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
return

chat_id = update.effective_chat.id  
group = get_group(chat_id)  

if not group["users"]:  
    await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")  
    return  

text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n"  
for i, uid in enumerate(group["users"], 1):  
    text += f"{i}. {uid}\n"  

await update.message.reply_text(text)

================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
message = update.message
if not message:
return

chat_id = message.chat.id  
user_id = message.from_user.id  
group = get_group(chat_id)  

if group["enabled"] and user_id in group["targets"]:  
    try:  
        await message.delete()  
    except:  
        pass

================= MAIN =================

load_data()

import os

TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("listuser", listuser))

app.add_handler(MessageHandler(filters.ALL, auto_delete))

print("BOT RUNNING...")
app.run_polling()
