import os
import asyncio
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

# ================= MONGODB =================
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# ================= STATE SEWA =================
user_state = {}
SEWA_PRICE = 5000

def get_group(chat_id):
    chat_id = str(chat_id)
    group = groups_col.find_one({"chat_id": chat_id})

    if not group:
        group = {
            "chat_id": chat_id,
            "targets": {},
            "allowed_users": {},
            "delete_on": False,
            "texts": [],
            "filter_text": False,
            "filter_foto": False,
            "expired_at": 0
        }
        groups_col.insert_one(group)

    return group

def save_group(group):
    groups_col.update_one(
        {"chat_id": group["chat_id"]},
        {"$set": group}
    )

# ================= HELPER =================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

# ================= DELAY DELETE =================
async def delay_delete(msg, delay):
    try:
        await asyncio.sleep(delay)
        await msg.delete()
    except:
        pass

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    await msg.reply_text(
        "SELAMAT DATANG DI BOT AUTODELETE KINGZAA\n"
        "KALAU MAU SEWA TINGGAL KETIK YAW🥰"
    )

# ================= SEWABOT (NEW FEATURE) =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    user_state[msg.from_user.id] = "wait_week"

    await msg.reply_text(
        "📦 SEWA BOT KINGZAA\n\n"
        "💰 1 MINGGU = 5K\n"
        "KIRIM ANGKA MINGGU YANG MAU DIBELI\n\n"
        "Contoh: 10"
    )

# ================= INPUT HANDLER SEWA =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id

    if msg.chat.type != "private":
        return

    if user_state.get(user_id) != "wait_week":
        return

    if not msg.text.isdigit():
        await msg.reply_text("KIRIM ANGKA AJA CONTOH: 5 / 10")
        return

    week = int(msg.text)
    total = week * SEWA_PRICE

    user_state[user_id] = None

    await msg.reply_text(
        "💳 PAYMENT KINGZAA\n\n"
        "DANA: 08888604716 AKBAR\n"
        f"NOMINAL: Rp {total}\n\n"
        f"KIRIM BUKTI KE {OWNER_USERNAME}"
    )

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
                return
            except:
                pass

    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            try:
                await msg.delete()
                return
            except:
                pass

    if group["filter_foto"] and msg.photo:
        try:
            await msg.delete()
            return
        except:
            pass

# ================= COMMAND ADD =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not msg.reply_to_message or not context.args:
        return

    target_id = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][target_id] = name
    save_group(group)

    await msg.reply_text("BERHASIL DITAMBAH")

# ================= COMMAND DELETE =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("BERHASIL DIHAPUS")
            return

# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = ""
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name}\n"

    await msg.reply_text(text or "KOSONG")

# ================= ADMIN =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER DITAMBAH")

# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = ""
    for uid, name in group["allowed_users"].items():
        text += f"- {name}\n"

    await msg.reply_text(text or "KOSONG")

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    target = context.args[0].lower()
    group = get_group(msg.chat.id)

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("USER DIHAPUS")
            return

# ================= TEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text not in group["texts"]:
        group["texts"].append(text)
        save_group(group)
        await msg.reply_text("TEXT DITAMBAH")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DIHAPUS")

async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = "\n".join(group["texts"])
    await msg.reply_text(text or "KOSONG")

# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_text"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("OK")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_foto"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("OK")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["delete_on"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("OK")

# ================= HANDLE =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("deluser", deluser))

app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))
app.add_handler(CommandHandler("alltext", alltext))

app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(~filters.COMMAND, handle_all), group=1)

print("BOT RUNNING...")
app.run_polling()
