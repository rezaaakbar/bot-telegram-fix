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
realtime_data = {}

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

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_data()
            await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            return

        if not context.args:
            await msg.reply_text("nama salah")
            return

        name = context.args[0].lower()
        found = False
        text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"

        for gid, gdata in data["groups"].items():
            for uid, uname in gdata["targets"].items():
                if uname == name:
                    text += f"{name} ({uid}) - GROUP {gid}\n"
                    found = True

        if not found:
            await msg.reply_text("nama salah")
        else:
            await msg.reply_text(text)
        return

    group = get_group(msg.chat.id)

    # 🔥 FILTER ADMIN
    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not group["targets"]:
        await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

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

    for uid, uname in list(group["allowed_users"].items()):
        if uname == name:
            del group["allowed_users"][uid]
            save_data()
            await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # 🔒 OWNER ONLY
    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻"")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n"
    found = False

    # 🔍 CEK SEMUA GROUP (BIAR BISA DI PRIVATE JUGA)
    for gid, gdata in data["groups"].items():
        for uid, name in gdata["allowed_users"].items():
            text += f"{name} ({uid}) - GROUP {gid}\n"
            found = True

    if not found:
        await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")
    else:
        await msg.reply_text(text)

# ================= ITUNGKATA =================

def reset_if_needed(chat_id):
    now = datetime.now().strftime("%Y-%m-%d")
    if chat_id not in realtime_data:
        realtime_data[chat_id] = {"date": now, "users": {}}
    elif realtime_data[chat_id]["date"] != now:
        realtime_data[chat_id] = {"date": now, "users": {}}

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    if msg.text.startswith("/"):
        return

    chat_id = str(msg.chat.id)
    reset_if_needed(chat_id)

    uid = str(msg.from_user.id)

    if uid not in realtime_data[chat_id]["users"]:
        realtime_data[chat_id]["users"][uid] = []

    realtime_data[chat_id]["users"][uid].append(msg.text.lower())

async def itungkata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("lu SIAPA ANJING‼️")
        return

    if not context.args:
        return

    keyword = context.args[0].lower()
    chat_id = str(msg.chat.id)
    reset_if_needed(chat_id)

    result = {}
    total = 0

    for uid, texts in realtime_data[chat_id]["users"].items():
        count = sum(text.count(keyword) for text in texts)
        if count > 0:
            result[uid] = count
            total += count

    if not result:
        await msg.reply_text("tidak ada data")
        return

    text = f"📊 Statistik Kata (Realtime)\n\n🔤 Kata: {keyword}\n\n"
    for uid, count in result.items():
        text += f"{uid} = {count}\n"

    text += f"\n📈 Total: {total} kali"
    await msg.reply_text(text)

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user:
        return

    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    if str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
        except Exception as e:
            print("DELETE ERROR:", e)

# ================= COMBINED HANDLER =================

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await track_message(update, context)
    await auto_delete(update, context)

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

app.add_handler(MessageHandler(filters.ALL, handle_all))

print("BOT RUNNING...")
app.run_polling()
