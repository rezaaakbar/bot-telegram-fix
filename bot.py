import os
import asyncio
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
            "delete_on": False,
            "masaaktif": {}
        }
        groups_col.insert_one(g)

    if "masaaktif" not in g:
        g["masaaktif"] = {}

    return g


def save_group(g):
    groups_col.update_one({"chat_id": g["chat_id"]}, {"$set": g})


def is_owner(id):
    return id == OWNER_ID


def is_allowed(id, g):
    return id == OWNER_ID or str(id) in g.get("allowed_users", {})

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
        if msg.text.lower().strip() in g.get("texts", []):
            try:
                await msg.delete()
            except:
                pass

    if g.get("filter_foto") and msg.photo:
        try:
            await msg.delete()
        except:
            pass

# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return

    if not msg.reply_to_message:
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    g["targets"][str(user.id)] = name
    save_group(g)

    await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELETE TARGET =================
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
            await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            return

# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    if not msg.reply_to_message:
        return

    if not context.args:
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    g["allowed_users"][str(user.id)] = {
        "name": name,
        "masaaktif": None
    }

    save_group(g)
    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")

# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()

    for g in groups_col.find():
        for uid, d in list(g.get("allowed_users", {}).items()):
            if isinstance(d, dict) and d.get("name") == name:
                del g["allowed_users"][uid]
        save_group(g)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")

# ================= MASA AKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    uid = context.args[0]
    date = " ".join(context.args[1:]).lower()

    g = get_group(msg.chat.id)

    if uid not in g.get("allowed_users", {}):
        await msg.reply_text("user tidak ditemukan di listuser")
        return

    if isinstance(g["allowed_users"][uid], dict):
        g["allowed_users"][uid]["masaaktif"] = date

    save_group(g)
    await msg.reply_text(f"{uid} aktif sampai {date}")

# ================= CEK MASA AKTIF =================
async def cekmasaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    g = get_group(msg.chat.id)
    uid = str(msg.from_user.id)

    data = g.get("allowed_users", {}).get(uid)

    if not isinstance(data, dict) or not data.get("masaaktif"):
        await msg.reply_text("𝗦𝗘𝗟𝗔𝗠𝗔𝗧 𝗞𝗔𝗠𝗨 𝗢𝗥𝗔𝗡𝗚 𝗧𝗘𝗥𝗣𝗜𝗟𝗜𝗛 𝗗𝗔𝗥𝗜 𝗕𝗢𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔")
        return

    await msg.reply_text(data["masaaktif"])

# ================= LISTUSER (FIXED 100%) =================
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
            if not name:
                continue

            masa = data.get("masaaktif")

            if masa:
                text += f"{name} (`{uid}`) {masa}\n"
            else:
                text += f"{name} (`{uid}`)\n"

        text += "\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for uid, name in g.get("targets", {}).items():
        text += f"{name} (`{uid}`)\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ================= ALLTEXT =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n"
    for i, t in enumerate(g.get("texts", []), 1):
        text += f"{i}. {t}\n"

    await update.message.reply_text(text)

# ================= ADDTEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, g):
        return

    t = " ".join(context.args).lower()
    g["texts"].append(t)
    save_group(g)

    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅")

# ================= DELTEXT =================
async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if not is_allowed(update.message.from_user.id, g):
        return

    t = " ".join(context.args).lower()

    if t in g.get("texts", []):
        g["texts"].remove(t)
        save_group(g)

    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")

# ================= FILTER TEXT =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if context.args[0] == "on":
        g["filter_text"] = True
        save_group(g)
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀")
    else:
        g["filter_text"] = False
        save_group(g)
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= FILTER FOTO =================
async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if context.args[0] == "on":
        g["filter_foto"] = True
        save_group(g)
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀")
    else:
        g["filter_foto"] = False
        save_group(g)
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= DELETE PESAN =================
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    g = get_group(update.message.chat.id)

    if not is_owner(update.message.from_user.id):
        return

    if context.args[0] == "on":
        g["delete_on"] = True
        save_group(g)
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀")
    else:
        g["delete_on"] = False
        save_group(g)
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

# ================= BOT RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("alltext", alltext))
app.add_handler(CommandHandler("addtext", addtext))
app.add_handler(CommandHandler("deltext", deltext))
app.add_handler(CommandHandler("filtertext", filtertext))
app.add_handler(CommandHandler("filterfoto", filterfoto))
app.add_handler(CommandHandler("deletepesan", deletepesan))
app.add_handler(CommandHandler("masaaktif", masaaktif))
app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif))

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
