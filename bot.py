import os
import time
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

# ================= DB =================
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

# ================= CLEAN EXPIRED =================
def clean_expired(group):
    now = time.time()
    changed = False

    if "premium_users" not in group:
        group["premium_users"] = {}

    for uid in list(group["premium_users"].keys()):
        if group["premium_users"][uid]["expire"] < now:
            del group["premium_users"][uid]
            changed = True

    if changed:
        save_group(group)

# ================= HELPER =================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

def is_premium(uid, group):
    return uid in group.get("premium_users", {})

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)
    clean_expired(group)

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

# ================= COMMAND TARGET =================
async def add(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("TIDAK DIIZINKAN")
        return

    if not msg.reply_to_message or not context.args:
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][uid] = name
    save_group(group)

    await msg.reply_text("BERHASIL")

async def delete(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("DIHAPUS")
            return

# ================= LISTUSN (TIDAK DIUBAH) =================
async def listusn(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    text = "LIST:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= USER =================
async def adduser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER ADD")

async def deluser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    target = context.args[0].lower()

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("USER DEL")
            return

async def listuser(update, context):
    msg = update.message

    text = ""
    for g in groups_col.find():
        for uid, name in g.get("allowed_users", {}).items():
            text += f"{g['chat_id']}\n{name}\n\n"

    await msg.reply_text(text)

# ================= TEXT =================
async def addtext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    group["texts"].append(" ".join(context.args).lower())
    save_group(group)

    await msg.reply_text("TEXT ADD")

async def deltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DEL")

async def alltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

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

    await msg.reply_text("OK")

async def filterfoto(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("OK")

async def deletepesan(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("OK")

# ================= PREMIUM =================
async def masaaktif(update, context):
    msg = update.message

    days = int(context.args[0])
    name = context.args[1].lower()

    match = re.findall(r"\((.*?)\)", msg.text)
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

        if uid in g.get("premium_users", {}):
            data = g["premium_users"][uid]

            sisa = int((data["expire"] - time.time()) / 86400)

            await msg.reply_text(
                f"NAMA: {data['name']}\n"
                f"GRUP: {g['chat_id']}\n"
                f"STATUS: AKTIF\n"
                f"SISA: {sisa} HARI"
            )
            return

    await msg.reply_text("EXPIRED / TIDAK PREMIUM")

async def listpremium(update, context):
    msg = update.message

    text = "LIST PREMIUM:\n"
    i = 0

    for g in groups_col.find():
        clean_expired(g)

        for uid, data in g.get("premium_users", {}).items():
            i += 1

            sisa = int((data["expire"] - time.time()) / 86400)

            status = "AKTIF" if sisa > 0 else "EXPIRED"

            text += (
    f"{i}.Nama: {data['name']}\n"
    f"UserID: {uid}\n"
    f"Grup: {g['chat_id']}\n"
    f"Status: {status}\n"
    f"Sisa: {sisa} hari\n\n"
            )

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
app.run_polling()
