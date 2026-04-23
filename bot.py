import os
import asyncio
import time
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
            "expired_at": 0
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

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    await msg.reply_text(
        "SELAMAT DATANG DI BOT AUTODELETE KINGZAA\n"
        "KALAU MAU SEWA TINGGAL KETIK YAW🥰"
    )

# ================= SEWA =================
async def sewa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    if not is_owner(msg.from_user.id):
        return

    if not context.args:
        await msg.reply_text("Contoh: /sewa -100xxxx (1 minggu = 5k)")
        return

    group_id = context.args[0]
    group = get_group(group_id)

    now = int(time.time())
    week = 7 * 24 * 60 * 60

    if group.get("expired_at", 0) > now:
        group["expired_at"] += week
    else:
        group["expired_at"] = now + week

    save_group(group)

    await msg.reply_text("SEWA AKTIF 1 MINGGU ✅")

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    # expired check
    if group.get("expired_at", 0) != 0:
        if int(time.time()) > group["expired_at"]:
            return

    if not msg.from_user:
        return

    # delete target
    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
                return
            except:
                pass

    # filter text
    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            try:
                await msg.delete()
                return
            except:
                pass

    # filter foto
    if group["filter_foto"] and msg.photo:
        try:
            await msg.delete()
            return
        except:
            pass

# ================= ADD =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"IZIN DULU {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    target_user = msg.reply_to_message.from_user
    target_id = str(target_user.id)
    name = context.args[0].lower()

    if target_user.id == OWNER_ID:
        await msg.reply_text("ITU BOSS GUA 😹")
        return

    group["targets"][target_id] = name
    save_group(group)

    bot_msg = await msg.reply_text("BERHASIL DITAMBAHKAN")
    asyncio.create_task(delay_delete(msg, 2))
    asyncio.create_task(delay_delete(bot_msg, 3))

# ================= DELETE =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"IZIN DULU {OWNER_USERNAME}")
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

    if not msg.reply_to_message or not context.args:
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER DITAMBAH")

# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    text = "LIST USER:\n"
    for uid, name in group["allowed_users"].items():
        text += f"- {name}\n"

    await msg.reply_text(text)

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    if not context.args:
        return

    target = context.args[0].lower()

    group = get_group(msg.chat.id)

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("USER DIHAPUS")
            return

# ================= ADDTEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text not in group["texts"]:
        group["texts"].append(text)
        save_group(group)
        await msg.reply_text("TEXT DITAMBAH")

# ================= DELTEXT =================
async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DIHAPUS")

# ================= ALLTEXT =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = "\n".join(group["texts"])
    await msg.reply_text(text if text else "KOSONG")

# ================= FILTER TEXT =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("OK")

# ================= FILTER FOTO =================
async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("OK")

# ================= DELETE PESAN =================
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("OK")

# ================= HANDLE =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewa", sewa))

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
