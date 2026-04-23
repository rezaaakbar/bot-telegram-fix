import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg or msg.chat.type == "private":
        return

    if not msg.from_user:
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
            return
        except:
            pass

# ================= MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📊 Menu")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🤖 BOT AKTIF\nKlik menu di bawah",
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Menu":
        keyboard = [
            [KeyboardButton("💰 Sewa Bot")],
            [KeyboardButton("📌 Info Bot")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("📋 MENU BOT:", reply_markup=reply_markup)

# ================= SEWA BOT =================
async def sewa_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "💰 Sewa Bot":
        keyboard = [
            [KeyboardButton("1 Minggu - 5K")],
            [KeyboardButton("2 Minggu - 10K")],
            [KeyboardButton("3 Minggu - 15K")],
            [KeyboardButton("4 Minggu - 20K")],
            [KeyboardButton("⬅️ Kembali")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("💰 Pilih Paket Sewa:", reply_markup=reply_markup)

async def pilih_sewa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "Minggu" in text:
        minggu = int(text.split()[0])
        harga = minggu * 5000

        await update.message.reply_text(
            f"""📦 DETAIL SEWA

Durasi: {minggu} Minggu
Harga: Rp {harga}

💳 Pembayaran:
DANA/OVO: 08xxxx

Kirim bukti ke:
{OWNER_USERNAME}
"""
        )

async def kembali(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ Kembali":
        await start(update, context)

# ================= COMMAND TARGET =================
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

    await msg.reply_text("✅ TARGET DITAMBAHKAN")

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
            save_group(group)
            await msg.reply_text("✅ TARGET DIHAPUS")
            return

# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not context.args:
        return

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await update.message.reply_text("✅ FILTER TEXT UPDATED")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not context.args:
        return

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await update.message.reply_text("✅ AUTO DELETE UPDATED")

# ================= HANDLE =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sewa_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pilih_sewa))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kembali))

app.add_handler(MessageHandler(~filters.COMMAND, handle_all), group=1)

print("BOT RUNNING...")
app.run_polling()
