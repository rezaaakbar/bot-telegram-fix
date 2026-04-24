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

# ================= RESPONSE =================
RESP = {
    "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀",
    "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰",
    "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛",
    "adduser": "𝗨𝗦𝗘𝗥 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛",
    "deluser": "𝗨𝗦𝗘𝗥 𝗗𝗜𝗛𝗔𝗣𝗨𝗦",
    "addtext": "TEXT DITAMBAH",
    "deltext": "TEXT DIHAPUS"
}

# ================= HELPER =================
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
    return g

def save_group(g):
    groups_col.update_one({"chat_id": g["chat_id"]}, {"$set": g})

def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})

async def reject(msg):
    await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")

async def success(msg, text):
    bot_msg = await msg.reply_text(text)
    await asyncio.sleep(1)
    try:
        await msg.delete()
        await bot_msg.delete()
    except:
        pass

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)

        if g.get("delete_on") and str(msg.from_user.id) in g["targets"]:
            await msg.delete()

        if g.get("filter_text") and msg.text:
            if msg.text.lower() in g["texts"]:
                await msg.delete()

        if g.get("filter_foto") and msg.photo:
            await msg.delete()

    except:
        pass

# ================= COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif. /help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/add (reply)\n"
        "/delete nama\n"
        "/listusn\n"
        "/deletepesan on/off\n"
        "/adduser (reply)\n"
        "/deluser nama\n"
    )

async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        return await msg.reply_text("Hubungi owner untuk sewa.")

    keyboard = [[InlineKeyboardButton("KONFIRMASI", callback_data="confirm")]]
    await msg.reply_text("SEWA BOT", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= TARGET =================

async def add(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return await msg.reply_text("Reply user")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower() if context.args else "no_name"

    g["targets"][uid] = name
    save_group(g)

    await success(msg, RESP["add"])

async def delete(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not context.args:
        return await msg.reply_text("Format: /delete nama")

    name = context.args[0].lower()

    for uid, n in list(g["targets"].items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)
            return await success(msg, RESP["delete"])

# ================= USER =================

async def adduser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return await msg.reply_text("Reply user")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower() if context.args else "user"

    g["allowed_users"][uid] = name
    save_group(g)

    await success(msg, RESP["adduser"])

async def deluser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not context.args:
        return await msg.reply_text("Format: /deluser nama")

    name = context.args[0].lower()

    for uid, n in list(g["allowed_users"].items()):
        if n == name:
            del g["allowed_users"][uid]
            save_group(g)
            return await success(msg, RESP["deluser"])

# ================= LIST =================

async def listusn(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text = "LIST TARGET:\n"
    for i, (uid, name) in enumerate(g["targets"].items(), 1):
        text += f"{i}. {name}\n"

    await msg.reply_text(text)

# ================= FILTER =================

async def deletepesan(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not context.args:
        return await msg.reply_text("on/off")

    g["delete_on"] = context.args[0] == "on"
    save_group(g)

    await success(msg, RESP["delete_on"] if g["delete_on"] else RESP["delete_off"])

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("sewabot", sewabot))

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))

app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
