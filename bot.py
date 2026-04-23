import os
import asyncio
import time
import re
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

    return group

def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})

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

    group = get_group(msg.chat.id)

    if group["delete_on"]:
        if str(msg.from_user.id) in group.get("targets", {}):
            try:
                await msg.delete()
            except:
                pass

# ================= TARGET =================
async def add(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][uid] = name
    save_group(group)

    await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")

async def delete(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗗𝗜𝗛𝗔𝗣𝗨𝗦")
            return

# ================= LISTUSN =================
async def listusn(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("𝗟𝗔𝗨")
        return

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            return

        if not context.args:
            return

        group = get_group(context.args[0])

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= USER =================
async def adduser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER ADD")

async def deluser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    target = context.args[0].lower()

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("USER DEL")
            return

async def listuser(update, context):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = ""

    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"({g['chat_id']})\n"
            for i, (uid, name) in enumerate(g["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"

    await msg.reply_text(text)

# ================= TEXT =================
async def addtext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)

    await msg.reply_text("TEXT ADD")

async def deltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DEL")

async def alltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            return

        if not context.args:
            return

        group = get_group(context.args[0])

    text = "LIST:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER =================
async def filtertext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("FILTER TEXT")

async def filterfoto(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("FILTER FOTO")

async def deletepesan(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("DELETE")

# ================= PREMIUM SYSTEM FIX =================
async def masaaktif(update, context):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    days = int(context.args[0])
    name = context.args[1].lower()

    match = re.findall(r"\((.*?)\)", msg.text)
    user_id = match[0]
    chat_id = match[1]

    group = get_group(chat_id)

    expire = time.time() + (days * 86400)

    group["premium_users"][user_id] = {
        "name": name,
        "expire": expire
    }

    save_group(group)

    await msg.reply_text(f"AKTIF {days} HARI")

# ================= CEK MASA AKTIF =================
async def cekmasaaktif(update, context):
    msg = update.message
    uid = str(msg.from_user.id)

    for g in groups_col.find():
        if uid in g.get("premium_users", {}):
            data = g["premium_users"][uid]

            expire = data["expire"]
            name = data["name"]

            now = time.time()

            status = "AKTIF" if now < expire else "EXPIRED"
            sisa = int((expire - now) / 86400) if now < expire else 0

            await msg.reply_text(
                f"NAMA: {name}\n"
                f"GRUP: {g['chat_id']}\n"
                f"STATUS: {status}\n"
                f"SISA: {sisa} HARI"
            )
            return

    await msg.reply_text("TIDAK PREMIUM")

# ================= LIST PREMIUM =================
async def listpremium(update, context):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = "📌 LIST PREMIUM:\n\n"
    i = 0

    for g in groups_col.find():
        for uid, data in g.get("premium_users", {}).items():
            i += 1

            now = time.time()
            status = "AKTIF" if now < data["expire"] else "EXPIRED"
            sisa = int((data["expire"] - now) / 86400) if now < data["expire"] else 0

            text += (
                f"{i}.\n"
                f"Nama: {data['name']}\n"
                f"UserID: {uid}\n"
                f"Grup: {g['chat_id']}\n"
                f"Status: {status}\n"
                f"Sisa: {sisa} hari\n\n"
            )

    await msg.reply_text(text)

# ================= HANDLER =================
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
app.run_polling()
