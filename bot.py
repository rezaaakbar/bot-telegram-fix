import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

data = {"groups": {}}
realtime_data = {}

DB_FILE = "database.json"

# ================= DATABASE =================

def load_data():
    global data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"groups": {}}
    else:
        data = {"groups": {}}

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= HELPER =================

def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {
            "targets": {},
            "allowed_users": {},
            "delete_on": False
        }
    return data["groups"][chat_id]

# ================= TRACK =================

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
        realtime_data[chat_id]["users"][uid] = {
            "username": msg.from_user.username,
            "name": msg.from_user.first_name,
            "texts": []
        }

    realtime_data[chat_id]["users"][uid]["texts"].append(msg.text.lower())

# ================= ITUNGKATA =================

async def itungkata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        if len(context.args) < 2:
            await msg.reply_text("format: /itungkata kata idgrup")
            return
        keyword = context.args[0].lower()
        chat_id = context.args[1]
    else:
        if not context.args:
            return
        keyword = context.args[0].lower()
        chat_id = str(msg.chat.id)

    group = get_group(chat_id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("lu siapa?")
        return

    reset_if_needed(chat_id)

    result = {}
    total = 0

    for uid, user_data in realtime_data.get(chat_id, {}).get("users", {}).items():
        texts = user_data["texts"]
        count = sum(text.count(keyword) for text in texts)
        if count > 0:
            result[uid] = (count, user_data)

    if not result:
        await msg.reply_text("tidak ada data")
        return

    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    now = datetime.now()

    text = f"""📊𝗝𝗨𝗠𝗟𝗔𝗛 𝗣𝗘𝗦𝗔𝗡 𝗛𝗔𝗥𝗜 𝗜𝗡𝗜
🗓️ {hari[now.weekday()]}, {now.strftime("%d-%m-%Y")}

📝𝗣𝗘𝗦𝗔𝗡 𝗬𝗚 𝗗𝗜 𝗖𝗔𝗥𝗜: {keyword}

"""

    for uid, (count, user_data) in result.items():
        username = user_data["username"]
        name = user_data["name"]

        tampil = f"@{username}" if username else name
        text += f"{tampil} = {count}\n"
        total += count

    text += f"\n🏆𝗧𝗢𝗧𝗔𝗟: {total}"

    await msg.reply_text(text)

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    if str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
        except:
            pass

# ================= COMMAND TARGET =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("tidak diizinkan")
        return

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["targets"][uid] = name
    save_data()

    await msg.reply_text("berhasil ditambahkan")

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
            await msg.reply_text("berhasil dihapus")
            return

# ================= ADMIN =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_data()

    await msg.reply_text("admin ditambahkan")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = "DAFTAR LIST USER:\n\n"
    found = False

    for gid, gdata in data["groups"].items():
        if gdata["allowed_users"]:
            text += f"({gid})\n"
            for i, (uid, name) in enumerate(gdata["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"
            text += "\n"
            found = True

    if not found:
        await msg.reply_text("kosong")
    else:
        await msg.reply_text(text)

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    if not context.args:
        return

    target = context.args[0]

    # hapus 1 grup
    if target.startswith("-100"):
        if target in data["groups"]:
            del data["groups"][target]
            save_data()
            await msg.reply_text("group dihapus")
        return

    # hapus nama
    group = get_group(msg.chat.id)

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_data()
            await msg.reply_text("user dihapus")
            return

# ================= LIST TARGET =================

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not group["targets"]:
        await msg.reply_text("kosong")
        return

    text = "DAFTAR LIST:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name}\n"

    await msg.reply_text(text)

# ================= DELETE ON OFF =================

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    if context.args[0] == "on":
        group["delete_on"] = True
    else:
        group["delete_on"] = False

    save_data()
    await msg.reply_text("ok")

# ================= MAIN =================

load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("deletepesan", deletepesan))
app.add_handler(CommandHandler("itungkata", itungkata))

app.add_handler(MessageHandler(filters.ALL, lambda u,c: track_message(u,c)))
app.add_handler(MessageHandler(filters.ALL, lambda u,c: auto_delete(u,c)))

print("BOT RUNNING...")
app.run_polling()
