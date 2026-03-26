import json
import os
import requests
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH", "database.json")

data = {"groups": {}}
user_group_map = {}

# ================= DATABASE =================

def load_data():
    global data, user_group_map
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            content = res.json()["content"]
            decoded = base64.b64decode(content).decode()
            db = json.loads(decoded)

            data = db.get("data", {"groups": {}})
            user_group_map = db.get("user_group_map", {})
        else:
            data = {"groups": {}}
            user_group_map = {}
    except:
        data = {"groups": {}}
        user_group_map = {}

def save_data():
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        db = {
            "data": data,
            "user_group_map": user_group_map
        }

        content = base64.b64encode(json.dumps(db, indent=2).encode()).decode()

        get_res = requests.get(url, headers=headers)
        sha = get_res.json().get("sha")

        payload = {
            "message": "update database",
            "content": content
        }

        if sha:
            payload["sha"] = sha

        requests.put(url, headers=headers, json=payload)

    except Exception as e:
        print("SAVE ERROR:", e)

# ================= HELPER =================

def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

def get_group(chat_id):
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = {
            "targets": {},
            "allowed_users": {},
            "delete_on": False
        }
    return data["groups"][str(chat_id)]

def get_target_input(update):
    msg = update.message

    # reply
    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
        return str(user.id), user.first_name

    # username / nama
    if msg.text.split():
        arg = msg.text.split()[1]
        if arg.startswith("@"):
            return None, arg
        return None, arg

    return None, None

# ================= COMMAND =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    user_id, name = get_target_input(update)

    if user_id:
        group["targets"][user_id] = name
        save_data()
        await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
        return

    # pakai nama
    for uid, uname in user_group_map.items():
        if uname.lower() == name.lower():
            group["targets"][uid] = name
            save_data()
            await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

    await msg.reply_text("User tidak ditemukan, reply pesan target dulu")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    name = msg.text.split()[1]

    for uid, uname in group["targets"].items():
        if uname == name:
            del group["targets"][uid]
            save_data()
            await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not group["targets"]:
        await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name}\n"

    await update.message.reply_text(text)

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, group):
        await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    arg = context.args[0]

    if arg == "on":
        group["delete_on"] = True
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦𝗦𝗦🚀")
    else:
        group["delete_on"] = False
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

    save_data()

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_owner(update.message.from_user.id):
        await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    user_id, name = get_target_input(update)

    if user_id:
        group["allowed_users"][user_id] = name
        user_group_map[user_id] = name
        save_data()
        await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_owner(update.message.from_user.id):
        await update.message.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    name = context.args[0]

    for uid, uname in group["allowed_users"].items():
        if uname == name:
            del group["allowed_users"][uid]
            save_data()
            await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not group["allowed_users"]:
        await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n"
    for i, (uid, name) in enumerate(group["allowed_users"].items(), 1):
        text += f"{i}. {name}\n"

    await update.message.reply_text(text)

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    if str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
        except:
            pass

# ================= MAIN =================

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
