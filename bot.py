import os
import time
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

# ================= DB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

# ================= RESPONSE STYLE =================
RESP = {
    "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀",
    "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰",
    "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅",
    "addtext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅",
    "deltext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "listusn": "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:",
    "alltext": "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓",
    "listuser": "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑"
}

# ================= DELAY =================
async def send_delay(msg, text, delay=3):
    await asyncio.sleep(delay)
    await msg.reply_text(text)

# ================= GROUP =================
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
            "premium_users": {}
        }
        groups_col.insert_one(group)

    if "premium_users" not in group:
        group["premium_users"] = {}

    return group

def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})

# ================= PREMIUM =================
def should_shutdown_group(group):
    now = time.time()
    for uid, data in group.get("premium_users", {}).items():
        if data["expire"] > now:
            return False
    return True

def clean_expired(group):
    now = time.time()

    for uid in list(group.get("premium_users", {})):
        if group["premium_users"][uid]["expire"] <= now:
            del group["premium_users"][uid]
            group.get("allowed_users", {}).pop(uid, None)
            group.get("targets", {}).pop(uid, None)

    save_group(group)

def is_allowed(user_id, group):
    uid = str(user_id)
    if user_id == OWNER_ID:
        return True
    return uid in group.get("allowed_users", {})

# ================= REJECT =================
async def reject(msg):
    await msg.reply_text(
        f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}"
    )

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)
    clean_expired(group)

    if should_shutdown_group(group):
        return

    if group.get("delete_on"):
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
            except:
                pass

    if group.get("filter_text") and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            try:
                await msg.delete()
            except:
                pass

    if group.get("filter_foto") and msg.photo:
        try:
            await msg.delete()
        except:
            pass

# ================= COMMANDS =================
async def add(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][uid] = name
    save_group(group)

    await send_delay(msg, RESP["add"], 3)

async def delete(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await send_delay(msg, RESP["delete"], 3)
            return

async def adduser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["allowed_users"][uid] = name
    save_group(group)

    await send_delay(msg, RESP["adduser"], 3)

async def deluser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    target = context.args[0].lower()

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await send_delay(msg, RESP["deluser"], 3)
            return

async def addtext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["texts"].append(" ".join(context.args).lower())
    save_group(group)

    await send_delay(msg, RESP["addtext"], 3)

async def deltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await send_delay(msg, RESP["deltext"], 3)

async def filtertext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await send_delay(msg, RESP["delete_on"] if group["filter_text"] else RESP["delete_off"], 3)

async def filterfoto(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await send_delay(msg, RESP["delete_on"] if group["filter_foto"] else RESP["delete_off"], 3)

async def deletepesan(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await send_delay(msg, RESP["delete_on"] if group["delete_on"] else RESP["delete_off"], 3)

# ================= PREMIUM =================
async def masaaktif(update, context):
    msg = update.message

    days = int(context.args[0])
    name = context.args[1].lower()

    match = re.findall(r"\(([^)]+)\)", msg.text)
    uid = match[0]
    gid = match[1]

    group = get_group(gid)

    group["premium_users"][uid] = {
        "name": name,
        "expire": time.time() + (days * 86400)
    }

    save_group(group)
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

    text = "LIST PREMIUM:\n\n"
    i = 0

    for g in groups_col.find():
        clean_expired(g)

        for uid, data in g.get("premium_users", {}).items():
            i += 1
            sisa = int((data["expire"] - time.time()) / 86400)

            text += f"{i}. Nama: {data['name']}\nUserID: {uid}\nGrup: {g['chat_id']}\nSisa: {sisa} hari\n\n"

    await msg.reply_text(text if i else "TIDAK ADA PREMIUM")

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))

app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))

app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))
app.add_handler(CommandHandler("listpremium", listpremium))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
