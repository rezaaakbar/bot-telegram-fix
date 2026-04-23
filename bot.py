import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# ================= MONTH =================
MONTHS = {
    "januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
    "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12
}

# ================= GET GROUP =================
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
            "masaaktif": {}
        }
        groups_col.insert_one(group)

    return group


def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})


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

# ================= AUTO DELETE + EXPIRE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    # ===== MASA AKTIF AUTO EXPIRE =====
    now = datetime.now().timestamp()
    expired = []

    for name, exp in group.get("masaaktif", {}).items():
        if now > exp:
            expired.append(name)

    for name in expired:
        for uid, uname in list(group["allowed_users"].items()):
            if uname == name:
                del group["allowed_users"][uid]
        del group["masaaktif"][name]

    save_group(group)

    if not group.get("allowed_users"):
        return

    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            await msg.delete()
            return

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

    await update.message.reply_text(
        "SELAMAT DATANG DI BOT KINGZAA KALAU MAU SEWA KETIK /SEWABOT"
    )

# ================= SEWABOT =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    await update.message.reply_text(
        "📦BOT KINGZAA\n\n"
        "⏳PERMINGGU 5K\n\n"
        "💸PAYMENT KINGZAA\n"
        "DANA:08888604716 AKBAR\n\n"
        f"TF SESUAI BERAPA MINGGU YG MAU DI SEWA‼️\n\n"
        f"KIRIM BUKTI KE {OWNER_USERNAME}"
    )

# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")

    target = msg.reply_to_message.from_user
    uid = str(target.id)
    name = context.args[0].lower()

    if target.id == OWNER_ID:
        return await msg.reply_text("𝗟𝗔𝗨 𝗦𝗢𝗞 𝗝𝗔𝗚𝗢?𝗜𝗡𝗜 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗟𝗔𝗪𝗔𝗞 😈")

    group["targets"][uid] = name
    save_group(group)

    bot = await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")
    asyncio.create_task(delay_delete(msg, 2))
    asyncio.create_task(delay_delete(bot, 3))

# ================= DELETE TARGET =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    name = context.args[0].lower()

    for uid, n in list(group["targets"].items()):
        if n == name:
            del group["targets"][uid]
            save_group(group)

            bot = await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            asyncio.create_task(delay_delete(msg, 2))
            asyncio.create_task(delay_delete(bot, 3))
            return

# ================= LIST TARGET =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for name in group["targets"].values():
        text += f"{name}\n"

    await update.message.reply_text(text)

# ================= ADD USER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return await msg.reply_text("𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗟𝗔𝗪𝗔𝗞😹")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DEL USER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()

    for uid, n in list(group["allowed_users"].items()):
        if n == name:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")
            return

# ================= LIST USER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n"
    for name in group["allowed_users"].values():
        text += f"{name}\n"

    await update.message.reply_text(text)

# ================= MASA AKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()
    day = int(context.args[1])
    month = MONTHS[context.args[2].lower()]

    exp = datetime(datetime.now().year, month, day).timestamp()

    for g in groups_col.find():
        if name in g.get("allowed_users", {}).values():
            g["masaaktif"][name] = exp
            save_group(g)

    await msg.reply_text(f"{name} aktif sampai {day}")

# ================= CEK MASA AKTIF =================
async def cekmasaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    uid = str(msg.from_user.id)
    if uid not in group["allowed_users"]:
        return await msg.reply_text("KAMU TIDAK TERDAFTAR")

    name = group["allowed_users"][uid]
    exp = group["masaaktif"].get(name)

    if not exp:
        return await msg.reply_text("SELAMAT KAMU PILIHAN KINGZAA 👑")

    remain = int((exp - datetime.now().timestamp()) / 86400)

    await msg.reply_text(f"MASA AKTIF {remain} HARI")

# ================= FILTER =================
async def filtertext(update, context):
    g = get_group(update.message.chat.id)
    g["filter_text"] = context.args[0] == "on"
    save_group(g)

    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if g["filter_text"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

async def filterfoto(update, context):
    g = get_group(update.message.chat.id)
    g["filter_foto"] = context.args[0] == "on"
    save_group(g)

    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if g["filter_foto"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

async def deletepesan(update, context):
    g = get_group(update.message.chat.id)
    g["delete_on"] = context.args[0] == "on"
    save_group(g)

    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if g["delete_on"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= HANDLER =================
async def handle(update, context):
    await auto_delete(update, context)

# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("listuser", listuser))

app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))

app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(filters.ALL, handle))

print("BOT RUNNING...")
app.run_polling()
