import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

data = {"groups": {}, "filters": []}
DB_FILE = "database.json"


# ================= DATABASE =================

def load_data():
    global data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"groups": {}, "filters": []}

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


# ================= AUTO DELETE TARGET =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    if not msg:
        return

    if msg.chat.type == "private":
        return

    group = get_group(msg.chat.id)

    if not group["delete_on"]:
        return

    uid = str(msg.from_user.id)

    if uid in group["targets"]:
        try:
            await msg.delete()
        except:
            pass


# ================= FILTER TEXT =================

async def filter_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    if not msg:
        return

    if not msg.text:
        return

    text = msg.text.lower()

    for word in data["filters"]:
        if word in text:
            try:
                await msg.delete()
            except:
                pass
            return


# ================= COMMAND TARGET =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
        return

    if not msg.reply_to_message:
        return

    if not context.args:
        return

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["targets"][uid] = name

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


async def listusn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if msg.chat.type == "private":

        if not is_owner(msg.from_user.id):
            await msg.reply_text(f"𝗟𝗔𝗨 𝗦𝗔𝗣𝗘 𝗔𝗡𝗝𝗜𝗡𝗚 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 𝗞𝗜𝗡𝗚𝗭𝗔𝗔 𝗗𝗨𝗟𝗨 {OWNER_USERNAME}")
            return

        text = "𝐃𝐀𝐅𝐓𝐀𝐑 𝐋𝐈𝐒𝐓:\n\n"
        found = False

        for gid, gdata in data["groups"].items():

            if gdata["targets"]:

                text += f"({gid})\n"

                for i, (uid, name) in enumerate(gdata["targets"].items(), 1):
                    text += f"{i}. {name} ({uid})\n"

                text += "\n"
                found = True

        if not found:
            await msg.reply_text("𝙈𝘼𝙎𝙄𝙃 𝙆𝙊𝙎𝙊𝙉𝙂 /𝙖𝙙𝙙 𝘿𝙐𝙇𝙐🤬")
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


# ================= ADMIN COMMAND =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    if not msg.reply_to_message:
        return

    if not context.args:
        return

    group = get_group(msg.chat.id)

    name = context.args[0].lower()
    uid = str(msg.reply_to_message.from_user.id)

    group["allowed_users"][uid] = name

    save_data()

    await msg.reply_text("ADMIN DITAMBAHKAN")


async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if not is_owner(msg.from_user.id):
        return

    text = "DAFTAR USER:\n\n"

    for gid, gdata in data["groups"].items():

        if gdata["allowed_users"]:

            text += f"({gid})\n"

            for i, (uid, name) in enumerate(gdata["allowed_users"].items(), 1):
                text += f"{i}. {name}\n"

            text += "\n"

    await msg.reply_text(text)


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

            save_data()

            await msg.reply_text("USER DIHAPUS")
            return


# ================= DELETE ON OFF =================

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    group = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, group):
        return

    if not context.args:
        return

    if context.args[0] == "on":
        group["delete_on"] = True
        await msg.reply_text("AUTO DELETE ON")

    elif context.args[0] == "off":
        group["delete_on"] = False
        await msg.reply_text("AUTO DELETE OFF")

    save_data()


# ================= FILTER COMMAND =================

async def addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    word = context.args[0].lower()

    if word not in data["filters"]:
        data["filters"].append(word)

        save_data()

        await update.message.reply_text("filter berhasil ditambahkan")


async def listfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not data["filters"]:
        await update.message.reply_text("filter kosong")
        return

    text = "LIST FILTER:\n"

    for i, w in enumerate(data["filters"], 1):
        text += f"{i}. {w}\n"

    await update.message.reply_text(text)


async def delfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    word = context.args[0].lower()

    if word in data["filters"]:
        data["filters"].remove(word)

        save_data()

        await update.message.reply_text("filter dihapus")


# ================= HANDLE ALL =================

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await auto_delete(update, context)
    await filter_text(update, context)


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

app.add_handler(CommandHandler("addfilter", addfilter))
app.add_handler(CommandHandler("listfilter", listfilter))
app.add_handler(CommandHandler("delfilter", delfilter))

app.add_handler(MessageHandler(filters.ALL, handle_all))

print("BOT RUNNING...")
app.run_polling()
