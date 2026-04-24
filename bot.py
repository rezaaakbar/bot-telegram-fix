import os
import time
import re
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# ================= MESSAGES =================
RESP = {
    "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀",
    "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰",
    "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "addtext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deltext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
}

# ================= CLEAN =================
async def clean_success(user_msg, bot_msg):
    try:
        await asyncio.sleep(2)
        await user_msg.delete()
    except:
        pass
    try:
        await asyncio.sleep(1)
        await bot_msg.delete()
    except:
        pass

# ================= GROUP =================
def get_group(chat_id):
    g = groups_col.find_one({"chat_id": str(chat_id)})
    if not g:
        g = {
            "chat_id": str(chat_id),
            "targets": {},
            "allowed_users": {},
            "delete_on": False,
            "texts": [],
            "filter_text": False,
            "filter_foto": False,
            "premium_users": {}
        }
        groups_col.insert_one(g)

    if "premium_users" not in g:
        g["premium_users"] = {}

    return g

def save_group(g):
    groups_col.update_one({"chat_id": g["chat_id"]}, {"$set": g})

# ================= PREMIUM =================
def clean_expired(g):
    now = time.time()

    if "premium_users" not in g:
        g["premium_users"] = {}

    for uid in list(g["premium_users"].keys()):
        exp = g["premium_users"][uid]["expire"]

        if exp != -1 and exp <= now:
            del g["premium_users"][uid]
            g.get("allowed_users", {}).pop(uid, None)
            g.get("targets", {}).pop(uid, None)

    save_group(g)

def shutdown(g, user_id=None):
    if user_id == OWNER_ID:
        return False

    now = time.time()
    premium_users = g.get("premium_users", {})

    if not premium_users:
        return True

    for _, data in premium_users.items():
        exp = data.get("expire", 0)

        if exp == -1 or exp > now:
            return False

    return True
    
def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)
        clean_expired(g)

        if shutdown(g, msg.from_user.id):
            return
    
        if g.get("delete_on") and str(msg.from_user.id) in g["targets"]:
            await msg.delete()

        if g.get("filter_text") and msg.text:
            if msg.text.lower() in g["texts"]:
                await msg.delete()

        if g.get("filter_foto") and msg.photo:
            await msg.delete()

    except:
        pass

# ================= WRAPPER =================
async def success(msg, text):
    bot_msg = await msg.reply_text(text)
    await clean_success(msg, bot_msg)

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
> ✨𝐒𝐄𝐋𝐀𝐌𝐀𝐓 𝐃𝐀𝐓𝐀𝐍𝐆✨
"""
    await update.message.reply_text(text)

async def sewabot(update, context):
    msg = update.message

    if msg.chat.type == "private":
        text = (
            "𝗟𝗜𝗦𝗧 𝗛𝗔𝗥𝗚𝗔 𝗕𝗢𝗧 𝗞𝗜𝗡𝗚𝗭𝗔𝗔:\n"
            "𝗣𝗘𝗥 𝗠𝗜𝗡𝗚𝗚𝗨 𝟱𝗞\n"
            "𝗣𝗘𝗥 𝗕𝗨𝗟𝗔𝗡 𝟭𝟱𝗞\n\n"
            "𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n"
            "DANA: 08888604716\n"
            f"QRIS: PM {OWNER_USERNAME}"
        )
        return await msg.reply_text(text)

    keyboard = [[InlineKeyboardButton("KONFIRMASI PEMBAYARAN", callback_data="confirm_sewa")]]
    await msg.reply_text("Klik tombol di bawah", reply_markup=InlineKeyboardMarkup(keyboard))

async def infobot(update, context):
    await update.message.reply_text("INFO BOT KINGZAA")

async def help_cmd(update, context):
    text = """
/add
/delete
/adduser
/deluser
/listusn
"""
    await update.message.reply_text(text)

async def tambahmasaaktif(update, context):
    msg = update.message
    name = context.args[0].lower()
    add_days = int(context.args[1])
    await msg.reply_text("BERHASIL TAMBAH MASA AKTIF")

async def kurangmasaaktif(update, context):
    await update.message.reply_text("BERHASIL KURANG MASA AKTIF")

async def add(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["targets"][uid] = name
    save_group(g)

    await success(msg, RESP["add"])

async def delete(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    name = context.args[0].lower()

    for uid, n in list(g["targets"].items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)
            await success(msg, RESP["delete"])
            return

async def listusn(update, context):
    g = get_group(update.message.chat.id)
    text = ""
    for i, (uid, name) in enumerate(g["targets"].items(), 1):
        text += f"{i}. {name}\n"
    await update.message.reply_text(text)

async def adduser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["allowed_users"][uid] = name
    save_group(g)

    await success(msg, RESP["adduser"])

async def deluser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    name = context.args[0].lower()

    for uid, n in list(g["allowed_users"].items()):
        if n == name:
            del g["allowed_users"][uid]
            save_group(g)
            await success(msg, RESP["deluser"])
            return

async def listuser(update, context):
    g = get_group(update.message.chat.id)
    text = ""
    for uid, name in g.get("allowed_users", {}).items():
        text += f"{name}\n"
    await update.message.reply_text(text)

async def addtext(update, context):
    g = get_group(update.message.chat.id)
    g["texts"].append(" ".join(context.args).lower())
    save_group(g)
    await success(update.message, RESP["addtext"])

async def deltext(update, context):
    g = get_group(update.message.chat.id)
    t = " ".join(context.args).lower()
    if t in g["texts"]:
        g["texts"].remove(t)
        save_group(g)
        await success(update.message, RESP["deltext"])

async def alltext(update, context):
    g = get_group(update.message.chat.id)
    text = "\n".join(g["texts"])
    await update.message.reply_text(text)

async def filtertext(update, context):
    g = get_group(update.message.chat.id)
    g["filter_text"] = context.args[0] == "on"
    save_group(g)
    await update.message.reply_text("DONE")

async def filterfoto(update, context):
    g = get_group(update.message.chat.id)
    g["filter_foto"] = context.args[0] == "on"
    save_group(g)
    await update.message.reply_text("DONE")

async def deletepesan(update, context):
    g = get_group(update.message.chat.id)
    g["delete_on"] = context.args[0] == "on"
    save_group(g)
    await update.message.reply_text("DONE")

async def masaaktif(update, context):
    await update.message.reply_text("MASA AKTIF DISET")

async def cekmasaaktif(update, context):
    await update.message.reply_text("CEK MASA AKTIF")

async def listpremium(update, context):
    await update.message.reply_text("LIST PREMIUM")

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))
app.add_handler(CommandHandler("infobot", infobot))
app.add_handler(CommandHandler("help", help_cmd))

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

app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))
app.add_handler(CommandHandler("listpremium", listpremium))

app.add_handler(CommandHandler("tambahmasaaktif", tambahmasaaktif))
app.add_handler(CommandHandler("kurangmasaaktif", kurangmasaaktif))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling(drop_pending_updates=True)
