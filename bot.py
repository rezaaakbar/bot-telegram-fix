import os
import asyncio
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

# ================= DELAY DELETE =================
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

    if not msg.from_user:
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
            try:
                await msg.delete()
                return
            except:
                pass

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
        await msg.reply_text(
            f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}"
        )
        return

    if not msg.reply_to_message or not context.args:
        return

    target_user = msg.reply_to_message.from_user
    target_id = str(target_user.id)
    name = context.args[0].lower()

    if target_user.id == OWNER_ID:
        await msg.reply_text("𝗛𝗔𝗛𝗔𝗛𝗔 𝗚𝗢𝗕𝗟𝗢𝗞 𝗜𝗧𝗨 𝗕𝗢𝗦𝗦 𝗚𝗨𝗔 𝗟𝗔𝗪𝗔𝗞😹😹😹")
        return

    group["targets"][target_id] = name
    save_group(group)

    bot_msg = await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
    asyncio.create_task(delay_delete(msg, 2))
    asyncio.create_task(delay_delete(bot_msg, 3))

# ================= DELETE =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(
            f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}"
        )
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)

            bot_msg = await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            asyncio.create_task(delay_delete(msg, 2))
            asyncio.create_task(delay_delete(bot_msg, 3))
            return

# ================= LISTUSN (COPY MODE) =================
async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚")
        return

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
            return

        if not context.args:
            await msg.reply_text("MASUKIN ID GRUP NYA BEGO\nContoh: /listusn -100xxxx")
            return

        group = get_group(context.args[0])

    if not group["targets"]:
        await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝘿 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n\n"
    text += "```USERLIST\n"

    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} | {uid}\n"

    text += "```"

    await msg.reply_text(text, parse_mode="Markdown")

# ================= FILTER TEXT =================
async def addtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)

    await msg.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")

async def deltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()
    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)

    await msg.reply_text("𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦")

async def alltext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐓𝐄𝐗𝐓:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER TOGGLE =================
async def filtertext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = context.args[0].lower() == "on"
    save_group(group)

    await msg.reply_text("𝗙𝗜𝗟𝗧𝗘𝗥 𝗧𝗘𝗫𝗧 𝗨𝗣𝗗𝗔𝗧𝗘")

async def filterfoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0].lower() == "on"
    save_group(group)

    await msg.reply_text("𝗙𝗜𝗟𝗧𝗘𝗥 𝗙𝗢𝗧𝗢 𝗨𝗣𝗗𝗔𝗧𝗘")

# ================= DELETE PESAN =================
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = context.args[0].lower() == "on"
    save_group(group)

    await msg.reply_text("𝗗𝗘𝗟𝗘𝗧𝗘 𝗠𝗢𝗗𝗘 𝗨𝗣𝗗𝗔𝗧𝗘")

# ================= HANDLER =================
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_delete(update, context)

app = ApplicationBuilder().token(TOKEN).build()

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

app.add_handler(MessageHandler(~filters.COMMAND, handle_all))

print("BOT RUNNING...")
app.run_polling()
