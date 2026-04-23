import os
import time
import re
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

# ================= PREMIUM =================
def is_premium_active(uid, group):
    data = group.get("premium_users", {}).get(uid)
    if not data:
        return False
    return data["expire"] > time.time()

def has_active_premium(group):
    now = time.time()
    for uid, data in group.get("premium_users", {}).items():
        if data["expire"] > now:
            return True
    return False

# ================= ACCESS =================
def is_allowed(user_id, group):
    uid = str(user_id)

    if user_id == OWNER_ID:
        return True

    if uid in group.get("premium_users", {}):
        if not is_premium_active(uid, group):
            return False

    return uid in group.get("allowed_users", {})

# ================= CLEAN EXPIRED =================
def clean_expired(group):
    now = time.time()

    for uid in list(group.get("premium_users", {})):
        if group["premium_users"][uid]["expire"] <= now:
            del group["premium_users"][uid]
            group.get("allowed_users", {}).pop(uid, None)
            group.get("targets", {}).pop(uid, None)

    save_group(group)

# ================= REJECT =================
async def reject(msg):
    await msg.reply_text(
        f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}"
    )

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)
    clean_expired(group)

    # 🔥 GROUP OFF IF NO PREMIUM ACTIVE
    if not has_active_premium(group):
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

# ================= COMMAND TARGET =================
async def add(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
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

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("DIHAPUS")
            return

# ================= LISTUSN =================
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

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER ADD")

async def deluser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
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

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["texts"].append(" ".join(context.args).lower())
    save_group(group)

    await msg.reply_text("TEXT ADD")

async def deltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)
    clean_expired(group)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DEL")

async def alltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    text = "LIST:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER =================
async def filtertext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["filter_text"] = context.args[0] == "on"
    save_group(group)
    await msg.reply_text("OK")

async def filterfoto(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)
    await msg.reply_text("OK")

async def deletepesan(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await reject(msg)
        return

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

        data = g.get("premium_users", {}).get(uid)
        if data:
            sisa = int((data["expire"] - time.time()) / 86400)

            await msg.reply_text(
                f"📌 STATUS PREMIUM ANDA:\n\n"
                f"NAMA: {data['name']}\n"
                f"GRUP: {g['chat_id']}\n"
                f"STATUS: AKTIF\n"
                f"SISA: {sisa} HARI"
            )
            return

    await msg.reply_text("❌ TIDAK PREMIUM / EXPIRED")

async def listpremium(update, context):
    msg = update.message

    text = "📌 LIST PREMIUM USER:\n\n"
    i = 0

    for g in groups_col.find():
        clean_expired(g)

        for uid, data in g.get("premium_users", {}).items():
            i += 1
            sisa = int((data["expire"] - time.time()) / 86400)

            text += (
                f"{i}.\n"
                f"Nama: {data['name']}\n"
                f"UserID: {uid}\n"
                f"Grup: {g['chat_id']}\n"
                f"Status: AKTIF\n"
                f"Sisa: {sisa} hari\n\n"
            )

    await msg.reply_text(text if i else "TIDAK ADA PREMIUM USER")

# ================= BOT =================
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
