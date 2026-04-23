import os
import asyncio
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

SEWA_PRICE = 5000
sewa_state = {}

# ================= MONGO =================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

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
            "filter_foto": False
        }
        groups_col.insert_one(group)

    return group

def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})

# ================= HELPER =================
def is_owner(uid):
    return uid == OWNER_ID

def is_allowed(uid, group):
    return uid == OWNER_ID or str(uid) in group.get("allowed_users", {})

# ================= DELAY DELETE =================
async def delay_delete(msg, delay):
    try:
        await asyncio.sleep(delay)
        await msg.delete()
    except:
        pass

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if not group.get("allowed_users"):
        return

    if group["delete_on"] and str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
            return
        except:
            pass

    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            await msg.delete()
            return

    if group["filter_foto"] and msg.photo:
        await msg.delete()
        return

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    await update.message.reply_text("SELAMAT DATANG DI BOT AUTODELETE KINGZAA🥰")

# ================= SEWA BOT =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    sewa_state[update.message.from_user.id] = 1

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data="min"),
            InlineKeyboardButton("1 MINGGU = 5K", callback_data="info"),
            InlineKeyboardButton("+", callback_data="plus")
        ],
        [InlineKeyboardButton("CONFIRM", callback_data="confirm")]
    ]

    await update.message.reply_text(
        "PILIH MENU DI BAWAH INI",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= CALLBACK =================
async def sewabot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if uid not in sewa_state:
        sewa_state[uid] = 1

    week = sewa_state[uid]

    if q.data == "plus":
        if week < 50:
            week += 1

    elif q.data == "min":
        if week > 1:
            week -= 1

    elif q.data == "info":
        await q.answer("1 MINGGU = 5K", show_alert=True)
        return

    elif q.data == "confirm":
        total = week * SEWA_PRICE
        await q.message.edit_text(
            f"PAYMENT KINGZAA\n\nDANA: 08888604716 AKBAR\nNOMINAL: {total}\n\nKIRIM BUKTI KE {OWNER_USERNAME}"
        )
        sewa_state.pop(uid, None)
        return

    sewa_state[uid] = week

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data="min"),
            InlineKeyboardButton(f"{week} MINGGU", callback_data="info"),
            InlineKeyboardButton("+", callback_data="plus")
        ],
        [InlineKeyboardButton("CONFIRM", callback_data="confirm")]
    ]

    await q.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ================= COMMANDS =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    if not is_allowed(update.message.from_user.id, group):
        return
    if update.message.reply_to_message and context.args:
        uid = str(update.message.reply_to_message.from_user.id)
        group["targets"][uid] = context.args[0].lower()
        save_group(group)
        await update.message.reply_text("BERHASIL DITAMBAH")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    if not is_allowed(update.message.from_user.id, group):
        return
    name = context.args[0].lower()
    for k,v in list(group["targets"].items()):
        if v == name:
            del group["targets"][k]
    save_group(group)
    await update.message.reply_text("BERHASIL DIHAPUS")

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = "\n".join([f"{k} - {v}" for k,v in group["targets"].items()])
    await update.message.reply_text(text or "KOSONG")

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    uid = str(update.message.reply_to_message.from_user.id)
    group["allowed_users"][uid] = context.args[0].lower()
    save_group(group)
    await update.message.reply_text("USER DITAMBAH")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    name = context.args[0].lower()
    for k,v in list(group["allowed_users"].items()):
        if v == name:
            del group["allowed_users"][k]
    save_group(group)
    await update.message.reply_text("USER DIHAPUS")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = "\n".join(group["allowed_users"].values())
    await update.message.reply_text(text or "KOSONG")

async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["texts"].append(" ".join(context.args).lower())
    save_group(group)
    await update.message.reply_text("TEXT DITAMBAH")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    t = " ".join(context.args).lower()
    if t in group["texts"]:
        group["texts"].remove(t)
    save_group(group)
    await update.message.reply_text("TEXT DIHAPUS")

async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    await update.message.reply_text("\n".join(group["texts"]) or "KOSONG")

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

# ================= HANDLER =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))
app.add_handler(CallbackQueryHandler(sewabot_callback))

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))
app.add_handler(CommandHandler("alltext", alltext))
app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(~filters.COMMAND, handle_all))

print("BOT RUNNING...")
app.run_polling()
