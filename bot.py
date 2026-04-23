import os
import asyncio
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

    if "masaaktif" not in group:
        group["masaaktif"] = {}

    return group


def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})


def is_owner(user_id):
    return user_id == OWNER_ID


# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    try:
        if group.get("delete_on"):
            await msg.delete()
    except:
        pass

    try:
        if group.get("filter_text") and msg.text:
            if msg.text.lower().strip() in group["texts"]:
                await msg.delete()
    except:
        pass

    try:
        if group.get("filter_foto") and msg.photo:
            await msg.delete()
    except:
        pass


# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    if not msg.reply_to_message:
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    group["targets"][str(user.id)] = name
    save_group(group)

    await msg.reply_text("𝗔𝗗𝗗 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")


# ================= DELETE TARGET =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            return


# ================= ADD USER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        return

    user = msg.reply_to_message.from_user
    name = context.args[0].lower()

    group["allowed_users"][str(user.id)] = {
        "name": name,
        "masaaktif": None
    }

    save_group(group)
    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")


# ================= DEL USER =================
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

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")


# ================= MASAAKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.from_user.id):
        return

    if len(context.args) < 2:
        return

    uid = context.args[0]
    date = " ".join(context.args[1:]).lower()

    group = get_group(update.message.chat.id)

    if uid not in group["allowed_users"]:
        await update.message.reply_text("user tidak ditemukan")
        return

    group["allowed_users"][uid]["masaaktif"] = date
    save_group(group)

    await update.message.reply_text(
        f"𝗠𝗔𝗦𝗔 𝗔𝗞𝗧𝗜𝗙 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Expired: {date}",
        parse_mode="HTML"
    )


# ================= LISTUSER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        text += f"({g['chat_id']})\n"

        for uid, data in g.get("allowed_users", {}).items():
            if isinstance(data, dict):
                name = data["name"]
                masa = data.get("masaaktif")

                if masa:
                    text += f"{name} (<code>{uid}</code>) {masa}\n"
                else:
                    text += f"{name} (<code>{uid}</code>)\n"

        text += "\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for uid, name in group["targets"].items():
        text += f"{name} (<code>{uid}</code>)\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ================= ALLTEXT =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await update.message.reply_text(text)


# ================= ADDTEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()

    group["texts"].append(text)
    save_group(group)

    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")


# ================= DELTEXT =================
async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)

    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗗𝗜𝗛𝗔𝗣𝗨𝗦")


# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_text"] = context.args[0] == "on"
    save_group(group)


async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_foto"] = context.args[0] == "on"
    save_group(group)


# ================= DELETEPESAN =================
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    if not is_owner(update.message.from_user.id):
        return

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    if context.args[0] == "on":
        await update.message.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀")
    else:
        await update.message.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")


# ================= MAIN =================
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

app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING...")
app.run_polling()
