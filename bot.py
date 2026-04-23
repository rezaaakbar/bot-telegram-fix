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

# ================= DATABASE =================
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


# ================= EXPIRED CHECK =================
def is_expired(date_str):
    try:
        now = datetime.now()
        parts = date_str.lower().split()

        day = int(parts[0])
        month = parts[1]

        months = {
            "jan":1,"january":1,
            "feb":2,"february":2,
            "mar":3,"march":3,
            "apr":4,"april":4,
            "may":5,"mei":5,
            "jun":6,"june":6,
            "jul":7,"july":7,
            "aug":8,"august":8,
            "sep":9,"september":9,
            "oct":10,"october":10,
            "nov":11,"november":11,
            "dec":12,"december":12
        }

        if month not in months:
            return False

        expire = datetime(now.year, months[month], day)
        return now > expire
    except:
        return False


# ================= ACCESS CHECK =================
def check_access(user_id, group):
    uid = str(user_id)

    if uid not in group.get("allowed_users", {}):
        return False

    name = group["allowed_users"][uid]
    date = group.get("masaaktif", {}).get(uid)

    if date and is_expired(date):
        del group["allowed_users"][uid]
        group["masaaktif"].pop(uid, None)
        save_group(group)
        return False

    return True


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


# ================= ADD =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not check_access(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user
    name = context.args[0].lower()

    group["targets"][str(target.id)] = name
    save_group(group)

    await msg.reply_text("𝗔𝗗𝗗 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")


# ================= DELETE =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")
            return


# ================= ADDUSER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text(f"𝗞𝗛𝗨𝗦𝗨𝗦 𝗢𝗪𝗡𝗘𝗥 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user
    name = context.args[0].lower()

    group["allowed_users"][str(target.id)] = name
    save_group(group)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅")


# ================= DELUSER =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    name = context.args[0].lower()

    for g in groups_col.find():
        for uid, uname in list(g.get("allowed_users", {}).items()):
            if uname == name:
                del g["allowed_users"][uid]
                save_group(g)

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧 ✅")


# ================= LISTUSN =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n"
    for uid, name in group["targets"].items():
        text += f"{name} ({uid})\n"

    await msg.reply_text(text)


# ================= ALLTEXT =================
async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    group = get_group(context.args[0])

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)


# ================= LISTUSER (FIXED) =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"({g['chat_id']})\n"

            for uid, name in g["allowed_users"].items():
                date = g.get("masaaktif", {}).get(uid)

                if date:
                    text += f"{name} ({uid}) {date}\n"
                else:
                    text += f"{name} ({uid})\n"

            text += "\n"

    await msg.reply_text(text)


# ================= FILTER TEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)
    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧 ✅")


async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    text = " ".join(context.args).lower()
    group["texts"].remove(text)
    save_group(group)
    await update.message.reply_text("𝗧𝗘𝗫𝗧 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅")


# ================= FILTER =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_text"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("𝗢𝗡" if group["filter_text"] else "𝗢𝗙𝗙")


async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)
    group["filter_foto"] = context.args[0] == "on"
    save_group(group)
    await update.message.reply_text("𝗢𝗡" if group["filter_foto"] else "𝗢𝗙𝗙")


# ================= MASAAKTIF =================
async def masaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.from_user.id):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    uid = str(user.id)
    date = " ".join(context.args).lower()

    group = get_group(update.message.chat.id)
    group["masaaktif"][uid] = date
    save_group(group)

    await update.message.reply_text(f"{user.first_name} aktif sampai {date}")


# ================= CEK =================
async def cekmasaaktif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = get_group(update.message.chat.id)

    for uid, date in group.get("masaaktif", {}).items():
        await update.message.reply_text(f"{uid} aktif sampai {date}")
        return

    await update.message.reply_text("selamat kamu org terpilih")


# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))

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
