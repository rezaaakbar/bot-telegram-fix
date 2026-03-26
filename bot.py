import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

DATA_FILE = "database.json"

data = {"groups": {}}
user_group_map = {}

def load_data():
    global data, user_group_map
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            db = json.load(f)
            data = db.get("data", {"groups": {}})
            user_group_map = db.get("user_group_map", {})
    else:
        data = {"groups": {}}
        user_group_map = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "data": data,
            "user_group_map": user_group_map
        }, f)

def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {
            "targets": {},
            "users": {},
            "enabled": False
        }
    return data["groups"][chat_id]

def is_owner(user_id):
    return user_id == OWNER_ID

def is_user(user_id, chat_id, group):
    return str(user_id) in group["users"] and user_group_map.get(str(user_id)) == str(chat_id)

async def get_target_id(update, context):
    msg = update.message

    if msg.reply_to_message:
        return msg.reply_to_message.from_user.id

    if context.args:
        arg = context.args[0]
        if arg.isdigit():
            return int(arg)
        try:
            member = await context.bot.get_chat_member(msg.chat.id, arg)
            return member.user.id
        except:
            return None

    return None

#================ COMMAND =================#

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    if not (is_owner(user_id) or is_user(user_id, chat_id, group)):
        await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    target_id = await get_target_id(update, context)
    if not target_id:
        return

    if target_id == OWNER_ID:
        return

    if str(target_id) in group["users"]:
        return

    alias = context.args[0] if context.args else str(target_id)

    group["targets"][str(target_id)] = alias
    save_data()

    await update.message.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    if not context.args:
        return

    name = context.args[0]

    found = None
    for uid, alias in group["targets"].items():
        if alias == name:
            found = uid
            break

    if found:
        del group["targets"][found]
        save_data()
        await update.message.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.effective_chat.id)

    if not group["targets"]:
        await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await update.message.reply_text(text)

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    if not (is_owner(user_id) or is_user(user_id, chat_id, group)):
        return

    if not context.args:
        return

    if context.args[0].lower() == "on":
        group["enabled"] = True
        save_data()
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦𝗦𝗦🚀")
    else:
        group["enabled"] = False
        save_data()
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

#================ OWNER =================#

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    target_id = await get_target_id(update, context)
    if not target_id:
        return

    alias = context.args[0] if context.args else str(target_id)

    group["users"][str(target_id)] = alias
    user_group_map[str(target_id)] = str(chat_id)
    save_data()

    await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    group = get_group(update.effective_chat.id)

    if not context.args:
        return

    name = context.args[0]

    found = None
    for uid, alias in group["users"].items():
        if alias == name:
            found = uid
            break

    if found:
        del group["users"][found]
        user_group_map.pop(found, None)
        save_data()
        await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    group = get_group(update.effective_chat.id)

    if not group["users"]:
        await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑 𝐘𝐆 𝐃𝐈 𝐓𝐀𝐌𝐁𝐀𝐇𝐊𝐀𝐍:\n"
    for i, (uid, name) in enumerate(group["users"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await update.message.reply_text(text)

#================ AUTO DELETE =================#

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    group = get_group(msg.chat.id)

    if group["enabled"] and str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
        except:
            pass

#================ MAIN =================#

load_data()

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
