import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

client = MongoClient(os.getenv("MONGO_URI"))
db = client["telegram_bot"]
groups_col = db["groups"]

# ================= GROUP =================
def get_group(chat_id):
    chat_id = str(chat_id)
    g = groups_col.find_one({"chat_id": chat_id})

    if not g:
        g = {
            "chat_id": chat_id,
            "targets": {},
            "allowed_users": {},
            "texts": [],
            "filter_text": False,
            "filter_foto": False,
            "delete_on": False
        }
        groups_col.insert_one(g)

    if "allowed_users" not in g:
        g["allowed_users"] = {}

    return g


def save_group(g):
    groups_col.update_one({"chat_id": g["chat_id"]}, {"$set": g})


def is_owner(user_id):
    return user_id == OWNER_ID


def is_allowed(user_id, g):
    return user_id == OWNER_ID or str(user_id) in g.get("allowed_users", {})

# ================= DURATION =================
def parse_duration(text):
    text = text.lower().strip()

    if text.endswith("d"):
        return timedelta(days=int(text[:-1]))
    if text.endswith("m"):
        return timedelta(days=int(text[:-1]) * 30)
    if text.endswith("y"):
        return timedelta(days=int(text[:-1]) * 365)

    return None

# ================= AUTO EXPIRED =================
async def check_expired():
    for g in groups_col.find():
        changed = False

        for uid, data in list(g.get("allowed_users", {}).items()):
            if not isinstance(data, dict):
                continue

            exp = data.get("masaaktif")

            if exp and datetime.utcnow().timestamp() > exp:
                del g["allowed_users"][uid]
                changed = True

        if changed:
            save_group(g)

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    g = get_group(msg.chat.id)

    if g.get("delete_on"):
        if str(msg.from_user.id) in g.get("targets", {}):
            try:
                await msg.delete()
            except:
                pass

    if g.get("filter_text") and msg.text:
        if msg.text.lower() in g.get("texts", []):
            try:
                await msg.delete()
            except:
                pass

    if g.get("filter_foto") and msg.photo:
        try:
            await msg.delete()
        except:
            pass

# ================= TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    g["targets"][str(user.id)] = name
    save_group(g)

    await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return

    name = context.args[0].lower()

    for uid, n in list(g.get("targets", {}).items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)

    await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗗𝗜𝗛𝗔𝗣𝗨𝗦")

# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    g["allowed_users"][str(user.id)] = {
        "name": name,
        "masaaktif": None
    }

    save_group(g)
    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()

    for g in groups_col.find():
        for uid, data in list(g.get("allowed_users", {}).items()):
            if isinstance(data, dict) and data.get("name") == name:
                del g["allowed_users"][uid]
        save_group(g)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗗𝗜𝗛𝗔𝗣𝗨𝗦")

# ================= MASA AKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    uid = context.args[0]
    dur = context.args[1]

    g = get_group(msg.chat.id)

    if uid not in g.get("allowed_users", {}):
        await msg.reply_text("user tidak ditemukan")
        return

    delta = parse_duration(dur)
    if not delta:
        await msg.reply_text("format salah")
        return

    exp = datetime.utcnow() + delta
    g["allowed_users"][uid]["masaaktif"] = exp.timestamp()

    save_group(g)
    await msg.reply_text("masa aktif di set")

# ================= CEK MASA AKTIF =================
async def cekmasaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)
    uid = str(msg.from_user.id)

    data = g.get("allowed_users", {}).get(uid)

    if not isinstance(data, dict) or not data.get("masaaktif"):
        await msg.reply_text("selamat kamu orang terpilih 😎")
        return

    exp = datetime.utcfromtimestamp(data["masaaktif"])
    await msg.reply_text(f"sisa {(exp - datetime.utcnow()).days} hari")

# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        allowed = g.get("allowed_users", {})

        if not allowed:
            continue

        text += f"({g['chat_id']})\n"

        for uid, data in allowed.items():

            if not isinstance(data, dict):
                continue

            name = data.get("name")
            masa = data.get("masaaktif")

            if masa:
                exp = datetime.utcfromtimestamp(masa).strftime("%Y-%m-%d")
                text += f"{name} ({uid}) {exp}\n"
            else:
                text += f"{name} ({uid})\n"

        text += "\n"

    await update.message.reply_text(text)

# ================= ADDTEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, g):
        return

    t = " ".join(context.args).lower()
    g["texts"].append(t)
    save_group(g)

    await update.message.reply_text("text ditambah")

# ================= DELTEXT =================
async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, g):
        return

    t = " ".join(context.args).lower()

    if t in g["texts"]:
        g["texts"].remove(t)
        save_group(g)

    await update.message.reply_text("text dihapus")

# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)
    g["filter_text"] = context.args[0] == "on"
    save_group(g)

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)
    g["filter_foto"] = context.args[0] == "on"
    save_group(g)

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)
    g["delete_on"] = context.args[0] == "on"
    save_group(g)

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))
app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING")
app.run_polling()
