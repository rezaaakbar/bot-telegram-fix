import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from pymongo import MongoClient

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

SEWA_PRICE = 5000
sewa_state = {}

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
            "filter_foto": False
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

    if msg.text:
        cmd = msg.text.split()[0].lower()
        if cmd in ["/listusn", "/listuser", "/alltext"]:
            return

    group = get_group(msg.chat.id)

    if not group.get("allowed_users"):
        return

    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
                return
            except:
                pass

    if group["filter_text"] and msg.text:
        if msg.text.lower().strip() in group["texts"]:
            await msg.delete()
            return

    if group["filter_foto"] and msg.photo:
        await msg.delete()
        return

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "SELAMAT DATANG DI BOT KINGZAA KALAU MAU SEWA KETIK /SEWABOT"
    )

# ================= SEWA BOT =================
async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    sewa_state[uid] = 1

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data="min"),
            InlineKeyboardButton("1 MINGGU = 5K", callback_data="info"),
            InlineKeyboardButton("+", callback_data="plus")
        ],
        [InlineKeyboardButton("CONFIRM", callback_data="confirm")]
    ]

    await update.message.reply_text(
        "📦BOT KINGZAA\n\n⏳PERMINGGU 5K\n\n💸PAYMENT KINGZAA\nDANA:08888604716 AKBAR\n\nTF SESUAI BERAPA MINGGU YG MAU DI SEWA‼️\n\nKALAU UDAH TF SS KIRIM BUKTI KE " + OWNER_USERNAME,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def sewabot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    week = sewa_state.get(uid, 1)

    if q.data == "plus":
        week += 1
    elif q.data == "min" and week > 1:
        week -= 1
    elif q.data == "confirm":
        total = week * SEWA_PRICE
        await q.message.edit_text(
            f"PAYMENT KINGZAA\n\nDANA:08888604716 AKBAR\nNOMINAL: {total}\n\nKIRIM BUKTI KE {OWNER_USERNAME}"
        )
        sewa_state.pop(uid, None)
        return

    sewa_state[uid] = week

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data="min"),
            InlineKeyboardButton(f"{week} MINGGU", callback_data="info"),
            InlineKeyboardButton("+", callback_data="plus")
        ],
        [InlineKeyboardButton("CONFIRM", callback_data="confirm")]
    ]

    await q.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")
        return

    target_user = msg.reply_to_message.from_user
    uid = str(target_user.id)
    name = context.args[0].lower()

    if target_user.id == OWNER_ID:
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗢𝗞 𝗝𝗔𝗚𝗢?𝗜𝗡𝗜 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗟𝗔𝗪𝗔𝗞 😈")
        return

    if uid in group["allowed_users"]:
        await msg.reply_text("𝗦𝗔𝗠𝗔 𝗦𝗔𝗠𝗔 𝗕𝗔𝗪𝗔𝗛𝗔𝗡 𝗚𝗔𝗨𝗦𝗔𝗛 𝗦𝗢𝗞 𝗝𝗔𝗚𝗢🖕")
        return

    group["targets"][uid] = name
    save_group(group)

    await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELETE TARGET =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            return

# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for i,(uid,name) in enumerate(group["targets"].items(),1):
        text += f"{i}. {name} ({uid})\n"
    await update.message.reply_text(text)

# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    uid = str(update.message.reply_to_message.from_user.id)
    name = context.args[0].lower()
    group["allowed_users"][uid] = name
    save_group(group)
    await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    name = context.args[0].lower()

    for uid, uname in list(group["allowed_users"].items()):
        if uname == name:
            del group["allowed_users"][uid]
            save_group(group)
            await update.message.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")
            return

# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"
    for i,(uid,name) in enumerate(group["allowed_users"].items(),1):
        text += f"{i}. {name}\n"
    await update.message.reply_text(text)

# ================= TEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)
    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()
    group["texts"].remove(text)
    save_group(group)
    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")

async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n"
    for i,t in enumerate(group["texts"],1):
        text += f"{i}. {t}\n"
    await update.message.reply_text(text)

# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_text"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if group["filter_text"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_foto"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀" if group["filter_foto"] else "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    f = group["filter_text"]
    p = group["filter_foto"]
    d = group["delete_on"]

    if d and f and p:
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀")
    else:
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= HANDLER =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sewabot", sewabot))
app.add_handler(CallbackQueryHandler(sewabot_callback))

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
