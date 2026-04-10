import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

data = {"groups": {}}
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
            "delete_on": False,
            "text_filters": []
        }
    return data["groups"][chat_id]

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    # delete target user
    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
                return
            except:
                pass

    # delete filtered text
    if msg.text:
        text = msg.text.lower()
        for word in group["text_filters"]:
            if word in text:
                try:
                    await msg.delete()
                    return
                except:
                    pass

# ================= TEXT FILTER =================

async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        await msg.reply_text("contoh: /addtext bio")
        return

    word = " ".join(context.args).lower()

    if word not in group["text_filters"]:
        group["text_filters"].append(word)
        save_data()

    await msg.reply_text("TEXT BERHASIL DITAMBAHKAN")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    word = " ".join(context.args).lower()

    if word in group["text_filters"]:
        group["text_filters"].remove(word)
        save_data()
        await msg.reply_text("TEXT BERHASIL DIHAPUS")
    else:
        await msg.reply_text("TEXT TIDAK DITEMUKAN")

async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not group["text_filters"]:
        await msg.reply_text("LIST FILTER MASIH KOSONG")
        return

    text = "LIST TEXT FILTER:\n\n"

    for i, word in enumerate(group["text_filters"], 1):
        text += f"{i}. {word}\n"

    await msg.reply_text(text)

# ================= TARGET SYSTEM =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["targets"][uid] = name
    save_data()

    await msg.reply_text("TARGET BERHASIL DITAMBAHKAN")

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
            await msg.reply_text("TARGET DIHAPUS")
            return

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not group["targets"]:
        await msg.reply_text("LIST KOSONG")
        return

    text = "DAFTAR TARGET:\n"

    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

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

    await msg.reply_text("ADMIN DITAMBAHKAN")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = "DAFTAR ADMIN:\n\n"

    for gid, gdata in data["groups"].items():
        if gdata["allowed_users"]:
            text += f"({gid})\n"
            for i, (uid, name) in enumerate(gdata["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"
            text += "\n"

    await msg.reply_text(text)

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    if not context.args:
        return

    target = context.args[0].lower()

    group = get_group(msg.chat.id)

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_data()
            await msg.reply_text("ADMIN DIHAPUS")
            return

# ================= DELETE SWITCH =================

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    if context.args[0] == "on":
        group["delete_on"] = True
        await msg.reply_text("AUTO DELETE AKTIF")
    else:
        group["delete_on"] = False
        await msg.reply_text("AUTO DELETE NONAKTIF")

    save_data()

# ================= HANDLE =================

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

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

app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))
app.add_handler(CommandHandler("alltext", alltext))

app.add_handler(MessageHandler(filters.ALL, handle_all))

print("BOT RUNNING...")
app.run_polling()
