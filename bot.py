import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN") or "ISI_TOKEN_KAMU"
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

# ================= MONGODB =================
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017"

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
    groups_col.update_one(
        {"chat_id": group["chat_id"]},
        {"$set": group}
    )

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg:
        return

    if msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if not group.get("allowed_users"):
        return

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
        except:
            pass

# ================= START MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_chat.type != "private":
        return

    keyboard = [
        [KeyboardButton("💰 Sewa Bot")],
        [KeyboardButton("📌 Info Bot")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🤖 BOT AKTIF\nPilih menu di bawah:",
        reply_markup=reply_markup
    )

# ================= MENU HANDLER =================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_chat.type != "private":
        return

    text = update.message.text

    if text == "💰 Sewa Bot":
        await update.message.reply_text(
            f"""💰 SEWA BOT

1 Minggu = 5K
2 Minggu = 10K
3 Minggu = 15K
4 Minggu = 20K

💳 Pembayaran:
DANA: 08888604716 akbar

📌 Kirim bukti transfer ke:
{OWNER_USERNAME}
"""
        )

    elif text == "📌 Info Bot":
        await update.message.reply_text(
            """📌 INFO BOT

Fitur Bot:
- Auto Delete Target
- Filter Text
- Filter Foto
- Management User

Cara Pakai:
Tambahkan bot ke grup lalu aktifkan fitur

Owner:
@KINGZAAASLI
"""
        )

# ================= GROUP COMMAND =================
def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not msg.reply_to_message or not context.args:
        return

    target_id = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][target_id] = name
    save_group(group)

    await msg.reply_text("✅ TARGET DITAMBAHKAN")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("✅ TARGET DIHAPUS")
            return

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    group = get_group(msg.chat.id)

    if
