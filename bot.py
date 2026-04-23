import os
import time
import re
import asyncio
import logging
from telegram import Update
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
    "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "addtext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deltext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
}

async def send(msg, text, delay=3):
    await asyncio.sleep(delay)
    await msg.reply_text(text)

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

# ================= PREMIUM SYSTEM =================
def clean_expired(g):
    now = time.time()
    if "premium_users" not in g:
        g["premium_users"] = {}

    for uid in list(g["premium_users"].keys()):
        if g["premium_users"][uid]["expire"] <= now:
            del g["premium_users"][uid]
            g.get("allowed_users", {}).pop(uid, None)
            g.get("targets", {}).pop(uid, None)

    save_group(g)

def shutdown(g):
    now = time.time()
    for _, d in g.get("premium_users", {}).items():
        if d["expire"] > now:
            return False
    return True

def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})

# ================= REJECT =================
async def reject(msg):
    await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)
        clean_expired(g)

        if shutdown(g):
            return

        if g.get("delete_on") and str(msg.from_user.id) in g["targets"]:
            await msg.delete()

        if g.get("filter_text") and msg.text:
            if msg.text.lower() in g["texts"]:
                await msg.delete()

        if g.get("filter_foto") and msg.photo:
            await msg.delete()

    except Exception as e:
        print("AUTO ERROR:", e)

# ================= COMMAND TARGET =================
async def add(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["targets"][uid] = name
    save_group(g)
    await send(msg, RESP["add"])

async def delete(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    name = context.args[0].lower()

    for uid, n in list(g["targets"].items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)
            await send(msg, RESP["delete"])
            return

async def listusn(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n\n"
    for i, (uid, name) in enumerate(g["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= USER =================
async def adduser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["allowed_users"][uid] = name
    save_group(g)
    await send(msg, RESP["adduser"])

async def deluser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    name = context.args[0].lower()

    for uid, n in list(g["allowed_users"].items()):
        if n == name:
            del g["allowed_users"][uid]
            save_group(g)
            await send(msg, RESP["deluser"])
            return

async def listuser(update, context):
    msg = update.message

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"
    for g in groups_col.find():
        for uid, name in g.get("allowed_users", {}).items():
            text += f"{g['chat_id']}\n{name}\n\n"

    await msg.reply_text(text)

# ================= TEXT =================
async def addtext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    g["texts"].append(" ".join(context.args).lower())
    save_group(g)
    await send(msg, RESP["addtext"])

async def deltext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    t = " ".join(context.args).lower()

    if t in g["texts"]:
        g["texts"].remove(t)
        save_group(g)
        await send(msg, RESP["deltext"])

async def alltext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n\n"
    for i, t in enumerate(g["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER =================
async def filtertext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    g["filter_text"] = context.args[0] == "on"
    save_group(g)
    await send(msg, RESP["delete_on"] if g["filter_text"] else RESP["delete_off"])

async def filterfoto(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    g["filter_foto"] = context.args[0] == "on"
    save_group(g)
    await send(msg, RESP["delete_on"] if g["filter_foto"] else RESP["delete_off"])

async def deletepesan(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    g["delete_on"] = context.args[0] == "on"
    save_group(g)
    await send(msg, RESP["delete_on"] if g["delete_on"] else RESP["delete_off"])

# ================= PREMIUM =================
async def masaaktif(update, context):
    msg = update.message

    days = int(context.args[0])
    name = context.args[1].lower()

    match = re.findall(r"\(([^)]+)\)", msg.text)
    uid = match[0]
    gid = match[1]

    g = get_group(gid)

    g["premium_users"][uid] = {
        "name": name,
        "expire": time.time() + (days * 86400)
    }

    save_group(g)
    await msg.reply_text("MASA AKTIF BERHASIL")

async def cekmasaaktif(update, context):
    msg = update.message
    uid = str(msg.from_user.id)

    for g in groups_col.find():
        clean_expired(g)

        data = g.get("premium_users", {}).get(uid)
        if data:
            sisa = int((data["expire"] - time.time()) / 86400)

            await msg.reply_text(
                f"NAMA: {data['name']}\nGRUP: {g['chat_id']}\nSTATUS: AKTIF\nSISA: {sisa} HARI"
            )
            return

    await msg.reply_text("EXPIRED / TIDAK PREMIUM")

async def listpremium(update, context):
    msg = update.message

    text = "𝐋𝐈𝐒𝐓 𝐏𝐑𝐄𝐌𝐈𝐔𝐌:\n\n"
    i = 1

    for g in groups_col.find():
        clean_expired(g)

        for uid, data in g.get("premium_users", {}).items():
            sisa = int((data["expire"] - time.time()) / 86400)

            text += f"{i}. Nama: {data['name']}\nUserID: {uid}\nGrup: {g['chat_id']}\nSisa: {sisa} hari\n\n"
            i += 1

    await msg.reply_text(text)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

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

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling(drop_pending_updates=True)
