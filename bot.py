import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

data = {"groups": {}}
realtime_data = {}

DB_FILE = "database.json"

# ================= DATABASE =================

def load_data():
    global data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"groups": {}}
    else:
        data = {"groups": {}}

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= HELPER =================

def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id, group):
    return user_id == OWNER_ID or str(user_id) in group.get("allowed_users", {})

def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {
            "targets": {},
            "allowed_users": {},
            "delete_on": False
        }
    return data["groups"][chat_id]

# ================= COMMAND =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        await msg.reply_text("Reply pesan target!")
        return

    if not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    if user_id == str(OWNER_ID):
        await msg.reply_text("𝗜𝗡𝗜 𝗕𝗢𝗦𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗧𝗢𝗟𝗢𝗟 𝗚𝗔 𝗕𝗜𝗦𝗔 𝗗𝗜 𝗔𝗗𝗗😹")
        return

    if user_id in group.get("allowed_users", {}):
        await msg.reply_text("𝗦𝗘𝗦𝗔𝗠𝗔 𝗣𝗘𝗡𝗚𝗚𝗨𝗡𝗔 𝗕𝗢𝗧 𝗚𝗔𝗕𝗜𝗦𝗔 𝗬𝗔 𝗔𝗦𝗨🥰")
        return

    group["targets"][user_id] = name
    save_data()
    await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not context.args:
        return

    name = context.args[0].lower()

    for uid, uname in list(group["targets"].items()):
        if uname == name:
            del group["targets"][uid]
            save_data()
            await msg.reply_text("𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")
            return

# ================= LIST TARGET =================

async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        if not is_owner(msg.from_user.id):
            await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
            return

        if not context.args:
            await msg.reply_text("nama salah")
            return

        name = context.args[0].lower()
        text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
        found = False

        for gid, gdata in data["groups"].items():
            for uid, uname in gdata["targets"].items():
                if uname == name:
                    text += f"{name} ({uid}) - GROUP {gid}\n"
                    found = True

        if not found:
            await msg.reply_text("nama salah")
        else:
            await msg.reply_text(text)
        return

    group = get_group(msg.chat.id)

    if not group["targets"]:
        await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙 𝘿𝙐𝙇𝙐🤬")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n"
    for i, (uid, name) in enumerate(group["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

# ================= ADMIN =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    if not msg.reply_to_message:
        await msg.reply_text("Reply pesan target!")
        return

    if not context.args:
        return

    name = context.args[0].lower()
    user_id = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][user_id] = name
    save_data()

    await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘 𝗗𝗔𝗙𝗧𝗔𝗥 𝗟𝗜𝗦𝗧✅")

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"
    found = False

    for gid, gdata in data["groups"].items():
        if gdata["allowed_users"]:
            text += f"({gid})\n"
            for i, (uid, name) in enumerate(gdata["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"
            text += "\n"
            found = True

    if not found:
        await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙𝙪𝙨𝙚𝙧 𝘿𝙐𝙇𝙐🤬")
    else:
        await msg.reply_text(text)

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not is_owner(msg.from_user.id):
        await msg.reply_text("𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬 𝗜𝗡𝗜 𝗞𝗛𝗨𝗦𝗨𝗦 𝗞𝗜𝗡𝗚𝗭𝗔𝗔🖕🏻")
        return

    if not context.args:
        return

    if msg.chat.type == "private":
        if len(context.args) < 2:
            await msg.reply_text("format: /deluser nama idgrup")
            return

        name = context.args[0].lower()
        gid = context.args[1]

        if gid in data["groups"]:
            group = data["groups"][gid]
            found = False

            for uid, uname in list(group["allowed_users"].items()):
                if uname == name:
                    del group["allowed_users"][uid]
                    found = True

            if not group["allowed_users"]:
                del data["groups"][gid]

            if found:
                save_data()
                await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦✅")
            else:
                await msg.reply_text("nama tidak ditemukan")
        else:
            await msg.reply_text("id grup tidak ditemukan")
        return

    target = context.args[0].lower()

    if target.startswith("-100"):
        if target in data["groups"]:
            del data["groups"][target]
            save_data()
            await msg.reply_text("𝗦𝗘𝗠𝗨𝗔 𝗔𝗗𝗠𝗜𝗡 𝗚𝗥𝗨𝗣 𝗗𝗜𝗛𝗔𝗣𝗨𝗦✅")
            return

    group = get_group(msg.chat.id)
    found = False

    for uid, name in list(group["allowed_users"].items()):
        if name == target:
            del group["allowed_users"][uid]
            found = True

    if not group["allowed_users"]:
        del data["groups"][str(msg.chat.id)]

    if found:
        save_data()
        await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦✅")
    else:
        await msg.reply_text("nama tidak ditemukan")

# ================= DELETE ON/OFF =================

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not context.args:
        return

    if context.args[0] == "on":
        group["delete_on"] = True
        await msg.reply_text("𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦𝗦𝗦🚀")
    else:
        group["delete_on"] = False
        await msg.reply_text("𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰")

    save_data()

# ================= TRACK =================

def reset_if_needed(chat_id):
    now = datetime.now().strftime("%Y-%m-%d")
    if chat_id not in realtime_data:
        realtime_data[chat_id] = {"date": now, "users": {}}
    elif realtime_data[chat_id]["date"] != now:
        realtime_data[chat_id] = {"date": now, "users": {}}

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    if msg.text.startswith("/"):
        return

    chat_id = str(msg.chat.id)
    reset_if_needed(chat_id)

    uid = str(msg.from_user.id)

    if uid not in realtime_data[chat_id]["users"]:
        realtime_data[chat_id]["users"][uid] = []

    realtime_data[chat_id]["users"][uid].append(msg.text.lower())

# ================= ITUNGKATA =================

async def itungkata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text("lu SIAPA ANJING‼️")
        return

    if not context.args:
        return

    keyword = context.args[0].lower()
    chat_id = str(msg.chat.id)
    reset_if_needed(chat_id)

    result = {}
    total = 0

    for uid, texts in realtime_data[chat_id]["users"].items():
        count = sum(text.count(keyword) for text in texts)
        if count > 0:
            result[uid] = count
            total += count

    if not result:
        await msg.reply_text("tidak ada data")
        return

    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    now = datetime.now()

    text = f"""📊𝗝𝗨𝗠𝗟𝗔𝗛 𝗣𝗘𝗦𝗔𝗡 𝗛𝗔𝗥𝗜 𝗜𝗡𝗜
🗓️ {hari[now.weekday()]}, {now.strftime("%d-%m-%Y")}

📝𝗣𝗘𝗦𝗔𝗡 𝗬𝗚 𝗗𝗜 𝗖𝗔𝗥𝗜: {keyword}

"""

    for uid, count in result.items():
        text += f"{uid} = {count}\n"

    text += f"\n🏆𝗧𝗢𝗧𝗔𝗟: {total}"
    await msg.reply_text(text)

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    if str(msg.from_user.id) in group["targets"]:
        try:
            await msg.delete()
        except:
            pass

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await track_message(update, context)
    await auto_delete(update, context)

# ================= MAIN =================

load_data()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("delete", delete))
app.add_handler(CommandHandler("listusn", listusn))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("listuser", listuser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("deletepesan", deletepesan))
app.add_handler(CommandHandler("itungkata", itungkata))

app.add_handler(MessageHandler(filters.ALL, handle_all))

print("BOT RUNNING...")
app.run_polling()
