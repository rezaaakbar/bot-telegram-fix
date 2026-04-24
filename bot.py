import os
import time
import re
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

#================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

#================= DATABASE =================

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
groups_col = db["groups"]

#================= RESPONSE =================

RESP = {
    "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀",
    "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰",
    "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "addtext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deltext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
}

#================= CLEAN SUCCESS =================

async def clean_success(user_msg, bot_msg):
    try:
        await asyncio.sleep(2)
        await user_msg.delete()
    except:
        pass

    try:
        await asyncio.sleep(1)
        await bot_msg.delete()
    except:
        pass

#================= GROUP =================

def get_group(chat_id):
    g = groups_col.find_one({"chat_id": str(chat_id)})

    if not g:
        g = {
            "chat_id": str(chat_id),
            "targets": {},
            "allowed_users": {},
            "delete_on": False,
            "texts": [],
            "filter_text": False,
            "filter_foto": False,
            "premium_users": {}
        }
        groups_col.insert_one(g)

    if "premium_users" not in g:
        g["premium_users"] = {}

    return g


def save_group(g):
    groups_col.update_one(
        {"chat_id": g["chat_id"]},
        {"$set": g}
    )

#================= PREMIUM =================

def clean_expired(g):
    now = time.time()

    if "premium_users" not in g:
        g["premium_users"] = {}

    for uid in list(g["premium_users"].keys()):
        exp = g["premium_users"][uid]["expire"]

        # SELAMANYA (-1) tidak dihapus
        if exp != -1 and exp <= now:
            del g["premium_users"][uid]
            g.get("allowed_users", {}).pop(uid, None)
            g.get("targets", {}).pop(uid, None)

    save_group(g)


def shutdown(g, user_id=None):
    # OWNER bypass
    if user_id == OWNER_ID:
        return False

    now = time.time()
    premium_users = g.get("premium_users", {})

    if not premium_users:
        return True

    for _, data in premium_users.items():
        exp = data.get("expire", 0)

        if exp == -1 or exp > now:
            return False

    return True


def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})

#================= REJECT =================

async def reject(msg):
    await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")

#================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message

        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)
        clean_expired(g)

        if shutdown(g, msg.from_user.id):
            return

        if g.get("delete_on") and str(msg.from_user.id) in g["targets"]:
            await msg.delete()

        if g.get("filter_text") and msg.text:
            if msg.text.lower() in g["texts"]:
                await msg.delete()

        if g.get("filter_foto") and msg.photo:
            await msg.delete()

    except:
        pass

#================= WRAPPER =================

async def success(msg, text):
    bot_msg = await msg.reply_text(text)
    await clean_success(msg, bot_msg)
    #================= COMMANDS UTAMA =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    text = (
        "> ✨𝐒𝐄𝐋𝐀𝐌𝐀𝐓 𝐃𝐀𝐓𝐀𝐍𝐆 𝐌𝐏𝐑𝐔𝐘 𝐃𝐈 𝐁𝐎𝐓 𝐊𝐈𝐍𝐆𝐙𝐀𝐀✨\n"
        "> •𝐊𝐀𝐋𝐀𝐔 𝐌𝐀𝐔 𝐒𝐄𝐖𝐀 𝐊𝐄𝐓𝐈𝐊 /sewabot\n"
        "> •𝐊𝐀𝐋𝐀𝐔 𝐌𝐀𝐔 𝐋𝐈𝐀𝐓 𝐈𝐍𝐅𝐎 𝐁𝐎𝐓/𝐅𝐔𝐍𝐆𝐒𝐈 𝐁𝐎𝐓 𝐊𝐄𝐓𝐈𝐊 /infobot\n"
        "> •𝐊𝐀𝐋𝐀𝐔 𝐌𝐀𝐔 𝐋𝐈𝐀𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐁𝐎𝐓 𝐊𝐄𝐓𝐈𝐊 /help\n"
        "> 𝐁𝐔𝐊𝐀𝐍 𝐁𝐎𝐓 𝐓𝐄𝐑𝐁𝐀𝐈𝐊 𝐓𝐀𝐏𝐈 𝐁𝐄𝐑𝐔𝐒𝐀𝐇𝐀 𝐌𝐄𝐍𝐉𝐀𝐃𝐈 𝐒𝐀𝐋𝐀𝐇 𝐒𝐀𝐓𝐔 𝐁𝐎𝐓 𝐓𝐄𝐑𝐁𝐀𝐈𝐊😁☺️"
    )

    await msg.reply_text(text)


#================= SEWABOT =================

async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # PRIVATE MODE
    if msg.chat.type == "private":
        text = (
            "𝗟𝗜𝗦𝗧 𝗛𝗔𝗥𝗚𝗔 𝗕𝗢𝗧 𝗞𝗜𝗡𝗚𝗭𝗔𝗔:\n"
            "𝗣𝗘𝗥 𝗠𝗜𝗡𝗚𝗚𝗨 𝟱𝗞\n"
            "𝗣𝗘𝗥 𝗕𝗨𝗟𝗔𝗡 𝟭𝟱𝗞\n\n"

            "𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗞𝗜𝗡𝗚𝗭𝗔𝗔:\n"
            "DANA: 08888604716\n"
            "GOPAY: KOSONG\n"
            "OVO : KOSONG\n"
            f"QRIS: PM {OWNER_USERNAME}\n\n"

            f"•𝗨𝗗𝗔𝗛 𝗧𝗙? 𝗞𝗜𝗥𝗜𝗠 𝗕𝗨𝗞𝗧𝗜 𝗞𝗘 {OWNER_USERNAME}\n"
            "•𝗞𝗔𝗟𝗔𝗨 𝗕𝗘𝗟𝗨𝗠 𝗗𝗜 𝗥𝗘𝗦𝗣𝗢𝗡 𝗧𝗨𝗡𝗚𝗚𝗨 𝗦𝗘𝗕𝗘𝗡𝗧𝗔𝗥\n"
            "•𝗝𝗔𝗡𝗚𝗔𝗡 𝗟𝗨𝗣𝗔 𝗧𝗔𝗠𝗕𝗔𝗛𝗜𝗡 𝗕𝗢𝗧𝗡𝗬𝗔 𝗞𝗘 𝗚𝗥𝗨𝗣 𝗬𝗔𝗪 "
            "𝗞𝗔𝗦𝗜𝗛 𝗔𝗞𝗦𝗘𝗦 𝗔𝗣𝗨𝗡 𝗣𝗘𝗦𝗔𝗡/𝗔𝗞𝗦𝗘𝗦 𝗔𝗟𝗟🥰"
        )

        return await msg.reply_text(text, parse_mode="Markdown")

    # GROUP MODE
    keyboard = [
        [InlineKeyboardButton("✅ KONFIRMASI PEMBAYARAN", callback_data="confirm_sewa")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "𝗟𝗜𝗦𝗧 𝗛𝗔𝗥𝗚𝗔 𝗕𝗢𝗧 𝗞𝗜𝗡𝗚𝗭𝗔𝗔:\n"
        "𝗣𝗘𝗥 𝗠𝗜𝗡𝗚𝗚𝗨 𝟱𝗞\n"
        "𝗣𝗘𝗥 𝗕𝗨𝗟𝗔𝗡 𝟭𝟱𝗞\n\n"

        "𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗞𝗜𝗡𝗚𝗭𝗔𝗔:\n"
        "DANA: 08888604716\n"
        "GOPAY: KOSONG\n"
        "OVO : KOSONG\n"
        f"QRIS: PM {OWNER_USERNAME}\n\n"

        "Setelah transfer,\n"
        "tekan tombol KONFIRMASI PEMBAYARAN di bawah 👇"
    )

    await msg.reply_text(text, reply_markup=reply_markup)


#================= INFOBOT =================

async def infobot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # PRIVATE ONLY
    if msg.chat.type != "private":
        return await msg.reply_text("COMMAND INI HANYA BISA DI PRIVATE BOT")

    text = (
        "𝗔𝗟𝗟 𝗜𝗡𝗙𝗢 𝗕𝗢𝗧 𝗞𝗜𝗡𝗚𝗭𝗔:\n\n"

        "𝙱𝙾𝚃 𝙸𝙽𝙸 𝙺𝙷𝚄𝚂𝚄𝚂 𝚄𝚃𝙰𝙼𝙰 𝙳𝚄𝙴𝙻𝙰𝙽+𝙺𝙰𝙽𝙶 𝙿𝚁𝙴𝙳 𝚈𝙰𝚆 𝙱𝚄𝙰𝚃 𝚈𝙶 𝚃𝙰𝙺𝚄𝚃 𝙰𝚂𝙸𝚂 𝙽𝚈𝙰 𝙶𝙰 𝚂𝙴𝙽𝙶𝙰𝙹𝙰 𝙰𝙿𝚄𝚂 𝙰𝙻𝙻 𝙿𝙴𝚂𝙰𝙽 𝙳𝙸 𝙶𝚁𝚄𝙿 𝚈𝙰𝚆\n\n"

        "𝚂𝙸𝚂𝚃𝙴𝙼𝙽𝚈𝙰 𝙸𝚃𝚄 𝚃𝙰𝚁𝙶𝙴𝚃, 𝙺𝙰𝙻𝙰𝚄 𝙰𝙳𝙰 𝚄𝚂𝙴𝚁 𝚈𝙶 𝙳𝙸 𝚃𝙰𝙽𝙳𝙰𝙸𝙽 𝙽𝙶𝙸𝚁𝙸𝙼 𝙿𝙴𝚂𝙰𝙽 𝙰𝙿𝙰𝙿𝚄𝙽 𝙱𝙸𝚂𝙰 𝚃𝙴𝚇𝚃, 𝙵𝙾𝚃𝙾, 𝚂𝚃𝙸𝙺𝙴𝚁, 𝙶𝙸𝙵 𝙳𝙻𝙻 𝙱𝙸𝚂𝙰 𝙳𝙸 𝙷𝙰𝙿𝚄𝚂\n\n"

        "𝙺𝙰𝙻𝙰𝚄 𝙼𝙰𝚄 𝙻𝙸𝙰𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳𝙽𝚈𝙰 𝙺𝙴𝚃𝙸𝙺 /help\n"
        f"𝙿𝙼 {OWNER_USERNAME} 𝙹𝙸𝙺𝙰 𝙼𝙰𝚄 𝙱𝙴𝙻𝙸/𝙿𝙴𝚁𝚃𝙰𝙽𝚈𝙰𝙰𝙽\n\n"

        "𝗠𝗜𝗡𝗔𝗧? 𝗦𝗨𝗡𝗚 𝗞𝗘𝗧𝗜𝗞 /sewabot"
    )

    await msg.reply_text(text)


#================= HELP =================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # PRIVATE ONLY
    if msg.chat.type != "private":
        return await msg.reply_text("COMMAND INI HANYA BISA DI PRIVATE BOT")

    uid = str(msg.from_user.id)

    # OWNER langsung lolos
    if uid != str(OWNER_ID):
        allowed = False

        # cek semua grup
        for g in groups_col.find():
            if uid in g.get("allowed_users", {}):
                allowed = True
                break

        if not allowed:
            return await msg.reply_text(
                f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}"
            )

    text = (
        "📌 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗛𝗘𝗟𝗣 𝗕𝗢𝗧\n\n"

        "🔹 /add (reply + nama)\n"
        "➡️ Tambah target user ke list auto delete\n\n"

        "🔹 /delete (nama)\n"
        "➡️ Hapus target dari list\n\n"

        "🔹 /listusn\n"
        "➡️ Lihat semua target\n\n"

        "🔹 /deletepesan on/off\n"
        "➡️ Aktif / matikan auto delete"
    )

    await msg.reply_text(text)

#================= TARGET =================

async def add(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["targets"][uid] = name
    save_group(g)

    await success(msg, RESP["add"])


async def delete(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    name = context.args[0].lower()

    for uid, n in list(g["targets"].items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)
            return await success(msg, RESP["delete"])


async def listusn(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐀𝐑𝐆𝐄𝐓:\n\n"

    for i, (uid, name) in enumerate(g["targets"].items(), 1):
        text += f"{i}. {name} ({uid})\n"

    await msg.reply_text(text)

#================= USER =================

async def adduser(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["allowed_users"][uid] = name
    save_group(g)

    await success(msg, RESP["adduser"])


async def deluser(update, context):
    msg = update.message

    # PRIVATE MODE
    if msg.chat.type == "private":

        if len(context.args) < 1:
            return await msg.reply_text("FORMAT: /deluser nama")

        name = context.args[0].lower()
        found = False

        for g in groups_col.find():
            changed = False

            for uid, n in list(g.get("allowed_users", {}).items()):
                if n == name:
                    del g["allowed_users"][uid]

                    if uid in g.get("premium_users", {}):
                        del g["premium_users"][uid]

                    if uid in g.get("targets", {}):
                        del g["targets"][uid]

                    changed = True
                    found = True

            if changed:
                groups_col.update_one(
                    {"chat_id": g["chat_id"]},
                    {"$set": g}
                )

        if found:
            return await msg.reply_text("𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗦𝗘𝗠𝗨𝗔 𝗚𝗥𝗨𝗣 ✅")

        return await msg.reply_text("USER TIDAK DITEMUKAN")

    # GROUP MODE
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    name = context.args[0].lower()

    for uid, n in list(g["allowed_users"].items()):
        if n == name:
            del g["allowed_users"][uid]

            if uid in g.get("premium_users", {}):
                del g["premium_users"][uid]

            if uid in g.get("targets", {}):
                del g["targets"][uid]

            save_group(g)
            return await success(msg, RESP["deluser"])

    await msg.reply_text("USER TIDAK DITEMUKAN")


async def listuser(update, context):
    msg = update.message

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        for uid, name in g.get("allowed_users", {}).items():
            text += f"{g['chat_id']}\n{name}\n\n"

    await msg.reply_text(text)

#================= TEXT =================

async def addtext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text_input = " ".join(context.args).lower()

    g["texts"].append(text_input)
    save_group(g)

    await success(msg, RESP["addtext"])


async def deltext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    t = " ".join(context.args).lower()

    if t in g["texts"]:
        g["texts"].remove(t)
        save_group(g)
        return await success(msg, RESP["deltext"])


async def alltext(update, context):
    msg = update.message
    g = get_group(msg.chat.id)

    text = "𝐋𝐈𝐒𝐓 𝐓𝐄𝐗𝐓:\n\n"

    for i, t in enumerate(g["texts"], 1):
        text += f"{i}. {t}\n"

    await msg.reply_text(text)
