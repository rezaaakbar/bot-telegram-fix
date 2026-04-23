import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

# ================= MONGO =================
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
            "filter_foto": False
        }
        groups_col.insert_one(group)

    return group

def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})

# ================= HELP =================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

# ================= DELETE =================
async def delay_delete(msg, t):
    await asyncio.sleep(t)
    try:
        await msg.delete()
    except:
        pass

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if not group.get("allowed_users"):
        return

    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
            except:
                pass

    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            await msg.delete()

    if group["filter_foto"] and msg.photo:
        await msg.delete()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    await update.message.reply_text(
        "SELAMAT DATANG DI BOT KINGZAA\nKALAU MAU SEWA KETIK /SEWABOT"
    )

# ================= SEWABOT =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    await update.message.reply_text(
        "📦BOT KINGZAA\n\n"
        "⏳PERMINGGU 5K\n\n"
        "💸PAYMENT KINGZAA\n"
        "DANA:08888604716 AKBAR\n\n"
        f"KIRIM BUKTI KE {OWNER_USERNAME}"
    )

# ================= ADD =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][uid] = name
    save_group(group)

    bot = await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")
    asyncio.create_task(delay_delete(msg, 2))
    asyncio.create_task(delay_delete(bot, 3))

# ================= DELETE =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)

            bot = await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            asyncio.create_task(delay_delete(msg, 2))
            asyncio.create_task(delay_delete(bot, 3))
            return

# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        if not context.args:
            return await msg.reply_text("MASUKIN ID GRUP\ncontoh: /listusn -100xxxx")
        group = get_group(context.args[0])
    else:
        group = get_group(msg.chat.id)

    text = "LIST TARGET:\n\n"
    for uid, name in group["targets"].items():
        text += f"{name} ({uid})\n"

    await msg.reply_text(text)

# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return await msg.reply_text(f"KHUSUS OWNER {OWNER_USERNAME}")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return await msg.reply_text(f"KHUSUS OWNER {OWNER_USERNAME}")

    name = context.args[0].lower()

    for uid, uname in list(group["allowed_users"].items()):
        if uname == name:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")
            return

# ================= LISTUSER (GLOBAL) =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.from_user.id):
        return await update.message.reply_text(f"KHUSUS OWNER {OWNER_USERNAME}")

    text = "LIST USER:\n\n"

    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"({g['chat_id']})\n"
            for uid, name in g["allowed_users"].items():
                text += f"- {name} ({uid})\n"
            text += "\n"

    await update.message.reply_text(text)

# ================= ADDTEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)

    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅")

# ================= DELTEXT =================
async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")

# ================= ALLTEXT =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        if not context.args:
            return await msg.reply_text("MASUKIN ID GRUP")
        group = get_group(context.args[0])
    else:
        group = get_group(msg.chat.id)

    text = "ALLTEXT:\n\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_text"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("DONE")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_foto"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("DONE")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["delete_on"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("DONE")

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))

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

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
