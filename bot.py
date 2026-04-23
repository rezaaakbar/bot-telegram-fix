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
            "group_expire": None
        }
        groups_col.insert_one(group)

    return group

def save_group(group):
    groups_col.update_one({"chat_id": group["chat_id"]}, {"$set": group})

# ================= HELPER =================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

def is_expired(group):
    exp = group.get("group_expire")
    return exp and asyncio.get_event_loop().time() > exp

async def check_expired(update, group):
    if is_expired(group):
        group["allowed_users"] = {}
        save_group(group)
        try:
            await update.message.reply_text("⛔ MASA AKTIF HABIS / BOT NONAKTIF")
        except:
            pass
        return True
    return False

# ================= AUTO DELETE =================
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if group["delete_on"]:
        if str(msg.from_user.id) in group["targets"]:
            try:
                await msg.delete()
            except:
                pass

# ================= ADD TARGET =================
async def add(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if await check_expired(update, group):
        return

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message or not context.args:
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    group["targets"][uid] = name
    save_group(group)

    await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡")

# ================= DELETE TARGET =================
async def delete(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if await check_expired(update, group):
        return

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_group(group)
            await msg.reply_text("𝗗𝗜𝗛𝗔𝗣𝗨𝗦")
            return

# ================= LISTUSN (FULL ORIGINAL LOGIC) =================
async def listusn(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if await check_expired(update, group):
        return

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("𝗟𝗔𝗨 𝗔𝗡𝗝𝗜𝗡𝗚")
        return

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 {OWNER_USERNAME}")
            return

        if not context.args:
            await msg.reply_text("MASUKIN ID GRUP\nContoh: /listusn -100xxxx")
            return

        group = get_group(context.args[0])

    if not group["targets"]:
        await msg.reply_text("𝙆𝙊𝙎𝙊𝙉𝙂 /𝘼𝘿𝘿 𝘿𝙐𝙇𝙐")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= ADDUSER =================
async def adduser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text("KHUSUS OWNER")
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name
    save_group(group)

    await msg.reply_text("USER DITAMBAH")

# ================= DELUSER =================
async def deluser(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    target = context.args[0].lower()

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            save_group(group)
            await msg.reply_text("USER DIHAPUS")
            return

# ================= LISTUSER (FULL ORIGINAL) =================
async def listuser(update, context):
    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = f"LIST USER ({msg.chat.id})\n\n"

    for g in groups_col.find():
        if g.get("allowed_users"):
            text += f"({g['chat_id']})\n"
            for i, (uid, name) in enumerate(g["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"
            text += "\n"

    await msg.reply_text(text)

# ================= ADDTEXT =================
async def addtext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()
    group["texts"].append(text)
    save_group(group)

    await msg.reply_text("TEXT DITAMBAH")

# ================= DELTEXT =================
async def deltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    text = " ".join(context.args).lower()

    if text in group["texts"]:
        group["texts"].remove(text)
        save_group(group)
        await msg.reply_text("TEXT DIHAPUS")

# ================= ALLTEXT (FULL ORIGINAL) =================
async def alltext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            return

        if not context.args:
            await msg.reply_text("MASUKIN ID GRUP")
            return

        group = get_group(context.args[0])

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, t in enumerate(group["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)

# ================= FILTER TEXT =================
async def filtertext(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_text"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("FILTER TEXT UPDATE")

# ================= FILTER FOTO =================
async def filterfoto(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["filter_foto"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("FILTER FOTO UPDATE")

# ================= DELETE PESAN =================
async def deletepesan(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    group["delete_on"] = context.args[0] == "on"
    save_group(group)

    await msg.reply_text("DELETE UPDATE")

# ================= MASA AKTIF =================
async def masaaktif(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        return

    days = int(context.args[0])
    group["group_expire"] = asyncio.get_event_loop().time() + (days * 86400)
    save_group(group)

    await msg.reply_text(f"AKTIF {days} HARI")

# ================= CEK MASA AKTIF =================
async def cekmasaaktif(update, context):
    msg = update.message
    group = get_group(msg.chat.id)

    exp = group.get("group_expire")

    if not exp:
        await msg.reply_text("TIDAK ADA PREMIUM")
        return

    sisa = exp - asyncio.get_event_loop().time()
    await msg.reply_text(f"SISA {int(sisa//86400)} HARI")

# ================= HANDLER =================
async def handle_all(update, context):
    await auto_delete(update, context)

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

app.add_handler(MessageHandler(~filters.COMMAND, handle_all))

print("BOT RUNNING...")
app.run_polling()
