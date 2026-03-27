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

# ================= WORD SYSTEM =================
word_data = {}
last_reset_date = datetime.now().date()

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

        payload = {
            "message": "update database",
            "content": content
        }

        if sha:
            payload["sha"] = sha

        requests.put(url, headers=headers, json=payload)

    except Exception as e:
        print("SAVE ERROR:", e)

# ================= RESET HARIAN =================

def check_reset():
    global word_data, last_reset_date

    now = datetime.now().date()

    if now != last_reset_date:
        word_data = {}
        last_reset_date = now
        print("RESET HARIAN 00:00")

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

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        await msg.reply_text("Reply pesan target!")
        return

    if not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    if user_id == str(OWNER_ID):
        await msg.reply_text("𝗜𝗡𝗜 𝗕𝗢𝗦𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗧𝗢𝗟𝗢𝗟 𝗚𝗔 𝗕𝗜𝗦𝗔 𝗗𝗜 𝗔𝗗𝗗😹")
        return

    if user_id in group.get("allowed_users", {}):
        await msg.reply_text("𝗦𝗘𝗦𝗔𝗠𝗔 𝗣𝗘𝗡𝗚𝗚𝗨𝗡𝗔 𝗕𝗢𝗧 𝗚𝗔𝗕𝗜𝗦𝗔 𝗬𝗔 𝗔𝗦𝗨🥰")
        return

    group["targets"][user_id] = name
    save_data()

    await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not context.args:
        return

    name = context.args[0].lower()

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
        text += f"{i}. {name} ({uid})\n"

    await update.message.reply_text(text)

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, group):
        await update.message.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not context.args:
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
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    if not msg.reply_to_message:
        await msg.reply_text("Reply pesan target!")
        return

    if not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][user_id] = name
    save_data()

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in group["allowed_users"].items():
        if uname == name:
            del group["allowed_users"][uid]
            save_data()
            await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not group["allowed_users"]:
        await update.message.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n"
    for i, (uid, name) in enumerate(group["allowed_users"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await update.message.reply_text(text)

# ================= ITUNGKATA =================

async def itungkata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_reset()

    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("lu SIAPA ANJING‼️")
        return

    if len(context.args) < 2:
        return

    target_word = context.args[0].lower()
    usernames = context.args[1:]

    chat_id = msg.chat.id
    text = "📊 Statistik Kata (Hari Ini)\n\n"
    text += f"🔤 Kata: {target_word}\n\n"

    counts = {}
    total = 0

    if chat_id in word_data:
        for user_id, words in word_data[chat_id].values():
            count = words.count(target_word)
            if count > 0:
                counts[user_id] = counts.get(user_id, 0) + count

    for uname in usernames:
        if not uname.startswith("@"):
            continue

        found = False

        for uid, c in counts.items():
            try:
                member = await context.bot.get_chat_member(chat_id, int(uid))
                if member.user.username and f"@{member.user.username.lower()}" == uname.lower():
                    text += f"{uname} = {c}\n"
                    total += c
                    found = True
                    break
            except:
                pass

        if not found:
            text += f"{uname} = 0\n"

    text += f"\n📈 Total: {total} kali"

    await msg.reply_text(text)

# ================= TRACK =================

async def track_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_reset()

    msg = update.message
    if not msg or not msg.text:
        return

    if msg.text.startswith("/"):
        return

    chat_id = msg.chat.id
    message_id = msg.message_id
    user_id = str(msg.from_user.id)

    words = msg.text.lower().split()

    if chat_id not in word_data:
        word_data[chat_id] = {}

    word_data[chat_id][message_id] = (user_id, words)

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    if str(msg.from_user.id) in group["targets"]:
        try:
            if msg.chat.id in word_data and msg.message_id in word_data[msg.chat.id]:
                del word_data[msg.chat.id][msg.message_id]

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

app.add_handler(MessageHandler(filters.ALL, auto_delete))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_words))

print("BOT RUNNING...")
app.run_polling()
