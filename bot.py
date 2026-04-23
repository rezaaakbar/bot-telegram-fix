import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

sewa_state = {}
SEWA_PRICE = 5000

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

    if msg.text:
        cmd = msg.text.split()[0].lower()
        if cmd in ["/listusn", "/listuser", "/alltext"]:
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
            await msg.delete()
            return

    if group["filter_foto"] and msg.photo:
        await msg.delete()
        return

# ================= START (NEW) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    await msg.reply_text(
        "SELAMAT DATANG DI BOT KINGZAA KALAU MAU SEWA KETIK /SEWABOT"
    )

# ================= SEWABOT (NEW) =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    await msg.reply_text(
        "📦BOT KINGZAA\n\n"
        "⏳PERMINGGU 5K\n\n"
        "💸PAYMENT KINGZAA\n"
        "DANA:08888604716 AKBAR\n\n"
        "TF SESUAI BERAPA MINGGU YG MAU DI SEWA‼️\n\n"
        f"KALAU UDAH TF SS KIRIM BUKTI KE {OWNER_USERNAME}"
    )

# ================= COMMAND TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"IZIN DULU KE {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    target_user = msg.reply_to_message.from_user
    target_id = str(target_user.id)
    name = context.args[0].lower()

    group["targets"][target_id] = name
    save_group(group)

    bot_msg = await msg.reply_text("BERHASIL DI TAMBAHKAN")
    asyncio.create_task(delay_delete(msg, 2))
    asyncio.create_task(delay_delete(bot_msg, 3))

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"IZIN DULU KE {OWNER_USERNAME}")
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)

            bot_msg = await msg.reply_text("BERHASIL DIHAPUS")
            asyncio.create_task(delay_delete(msg, 2))
            asyncio.create_task(delay_delete(bot_msg, 3))
            return

# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    text = "LIST TARGET:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER DITAMBAHKAN")

# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    text = "LIST USER:\n"
    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"\n({g['chat_id']})\n"
            for i, (uid, name) in enumerate(g["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"

    await msg.reply_text(text)

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    target = context.args[0].lower()

    for group in groups_col.find():
        for uid, name in list(group.get("allowed_users", {}).items()):
            if name == target:
                del group["allowed_users"][uid]
                save_group(group)

    await msg.reply_text("USER DIHAPUS")

# ================= FILTER TEXT =================
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

async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = not group["filter_text"]
    save_group(group)

    await msg.reply_text("FILTER TEXT TOGGLE")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = not group["filter_foto"]
    save_group(group)

    await msg.reply_text("FILTER FOTO TOGGLE")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = not group["delete_on"]
    save_group(group)

    await msg.reply_text("DELETE MODE TOGGLE")

# ================= HANDLE =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

# NEW
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))

# OLD COMMANDS (FULL KEEP)
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
