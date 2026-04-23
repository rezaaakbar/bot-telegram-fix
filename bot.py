import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

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
            "texts": [],
            "filter_text": False,
            "filter_foto": False,
            "delete_on": False,
            "masaaktif": {}
        }
        groups_col.insert_one(group)

    return group


def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})


def is_owner(user_id):
    return user_id == OWNER_ID


def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

# ================= DELETE HELPER =================
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

    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            await msg.delete()

    if group["filter_foto"] and msg.photo:
        await msg.delete()

# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")
        return

    target = msg.reply_to_message.from_user
    name = context.args[0].lower()

    group["targets"][str(target.id)] = name
    save_group(group)

    await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELETE TARGET =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            return

# ================= LISTUSN (OWNER ONLY PRIVATE) =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔😹")
        return

    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for uid, name in group["targets"].items():
        text += f"{name} ({uid})\n"

    await msg.reply_text(text)

# ================= ALLTEXT (OWNER ONLY PRIVATE) =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔😹")
        return

    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= LISTUSER (OWNER ONLY PRIVATE) =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔😹")
        return

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"({g['chat_id']})\n"
            for name in g["allowed_users"].values():
                text += f"{name}\n"
            text += "\n"

    await msg.reply_text(text)

# ================= FILTER TEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)

    await msg.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()
    group["texts"].remove(text)
    save_group(group)

    await msg.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")

# ================= FILTER TOGGLE =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if group["filter_text"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if group["filter_foto"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= MASAAKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.from_user.id):
        return

    group = get_group(context.args[0])
    name = context.args[1]
    date = context.args[2]

    group["masaaktif"][name] = date
    save_group(group)

    await update.message.reply_text(f"{name} aktif sampai {date}")

# ================= CEK MASAAKTIF =================
async def cekmasaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    uid = str(msg.from_user.id)

    for name, date in group.get("masaaktif", {}).items():
        await msg.reply_text(f"{name} aktif sampai {date}")
        return

    await msg.reply_text("selamat kamu org terdekat dan terpilih dari bos kingzaa")

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))

app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("alltext", alltext))
app.add_handler(CommandHandler("listuser", listuser))

app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))

app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))

app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
