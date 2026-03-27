import json
import os
import requests
import base64
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH", "database.json")

data = {"groups": {}}
word_stats = {}  # realtime (tidak disimpan)

# ================= DATABASE =================

def load_data():
    global data
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            content = res.json()["content"]
            decoded = base64.b64decode(content).decode()
            db = json.loads(decoded)
            data = db.get("data", {"groups": {}})
        else:
            data = {"groups": {}}
    except:
        data = {"groups": {}}

def save_data():
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        db = {"data": data}
        content = base64.b64encode(json.dumps(db, indent=2).encode()).decode()

        get_res = requests.get(url, headers=headers)
        sha = get_res.json().get("sha")

        payload = {"message": "update database", "content": content}
        if sha:
            payload["sha"] = sha

        requests.put(url, headers=headers, json=payload)
    except:
        pass

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

# ================= COMMAND =================

# ADD TARGET
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    if user_id == str(OWNER_ID):
        await msg.reply_text("𝗜𝗡𝗜 𝗕𝗢𝗦𝗦😹")
        return

    group["targets"][user_id] = name
    save_data()

    await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡✅")

# DELETE TARGET
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_data()
            await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦✅")
            return

# LIST TARGET
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if context.args:
        name = context.args[0].lower()
        found = False
        text = "𝐃𝐀𝐅𝐓𝐀𝐑:\n"

        for gid, group in data["groups"].items():
            for uid, uname in group["targets"].items():
                if uname == name:
                    text += f"{uname} ({uid}) - {gid}\n"
                    found = True

        if not found:
            await msg.reply_text("nama salah")
        else:
            await msg.reply_text(text)
        return

    group = get_group(msg.chat.id)

    if not group["targets"]:
        await msg.reply_text("𝙆𝙊𝙎𝙊𝙉𝙂")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# DELETE ON OFF
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, group):
        return

    if not context.args:
        return

    if context.args[0] == "on":
        group["delete_on"] = True
        await update.message.reply_text("𝗢𝗡🚀")
    else:
        group["delete_on"] = False
        await update.message.reply_text("𝗢𝗙𝗙🥰")

    save_data()

# ADD USER (OWNER ONLY)
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text("KHUSUS OWNER")
        return

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][user_id] = name
    save_data()

    await msg.reply_text("USER DITAMBAHKAN")

# DEL USER
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["allowed_users"].items()):
        if uname == name:
            del group["allowed_users"][uid]
            save_data()
            await msg.reply_text("USER DIHAPUS")
            return

# LIST USER
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not group["allowed_users"]:
        await update.message.reply_text("KOSONG")
        return

    text = "LIST USER:\n"
    for i, (uid, name) in enumerate(group["allowed_users"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await update.message.reply_text(text)

# ================= ITUNGKATA =================

async def itungkata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("lu SIAPA ANJING‼️")
        return

    if len(context.args) < 2:
        return

    kata = context.args[0].lower()
    usernames = context.args[1:]

    chat_id = str(msg.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    result = f"📊 Statistik Kata\nKata: {kata}\n\n"
    total = 0

    for user in usernames:
        count = word_stats.get(chat_id, {}).get(today, {}).get(user, {}).get(kata, 0)
        result += f"{user} = {count}\n"
        total += count

    result += f"\nTotal: {total}"

    await msg.reply_text(result)

# ================= TRACK CHAT =================

async def tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text:
        return

    text = msg.text.lower()
    if text.startswith("/"):
        return

    chat_id = str(msg.chat.id)
    user = f"@{msg.from_user.username}" if msg.from_user.username else str(msg.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in word_stats:
        word_stats[chat_id] = {}
    if today not in word_stats[chat_id]:
        word_stats[chat_id][today] = {}
    if user not in word_stats[chat_id][today]:
        word_stats[chat_id][today][user] = {}

    words = text.split()
    for w in words:
        word_stats[chat_id][today][user][w] = word_stats[chat_id][today][user].get(w, 0) + 1

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
app.add_handler(CommandHandler("itungkata", itungkata))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tracker))
app.add_handler(MessageHandler(filters.ALL, auto_delete))

print("BOT RUNNING...")
app.run_polling()
