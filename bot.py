import os import time import re import asyncio import logging from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN") MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079 OWNER_USERNAME = "@KINGZAAASLI"

client = MongoClient(MONGO_URI) db = client["telegram_bot"] groups_col = db["groups"]

================= RESPONSE (SAMAIN DENGAN AWAL KODE KAMU) =================

RESP = { "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀", "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰", "delete": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅", "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅", "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅", "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅", "addtext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅", "deltext": "𝗧𝗘𝗫𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅", }

================= DATABASE =================

def get_group(chat_id): g = groups_col.find_one({"chat_id": str(chat_id)}) if not g: g = { "chat_id": str(chat_id), "targets": {}, "allowed_users": {}, "delete_on": False, "texts": [], "filter_text": False, "filter_foto": False, "premium_users": {} } groups_col.insert_one(g)

if "premium_users" not in g:
    g["premium_users"] = {}

return g

def save_group(g): groups_col.update_one({"chat_id": g["chat_id"]}, {"$set": g})

================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE): try: msg = update.message if not msg or msg.chat.type == "private": return

g = get_group(msg.chat.id)

    if g.get("delete_on") and str(msg.from_user.id) in g["targets"]:
        await msg.delete()

    if g.get("filter_text") and msg.text:
        if msg.text.lower() in g["texts"]:
            await msg.delete()

    if g.get("filter_foto") and msg.photo:
        await msg.delete()

except:
    pass

================= START / HELP / INFO =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("✨ SELAMAT DATANG DI BOT KINGZAA")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "/add /delete /adduser /deluser\n" "/listuser /listusn /addtext /deltext\n" "/deletepesan /filtertext /filterfoto\n" "/listpremium /cekmasaaktif /masaaktif" )

async def infobot(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("BOT AUTO DELETE + PREMIUM SYSTEM + FILTER ACTIVE")

================= SEWABOT =================

async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE): msg = update.message

if msg.chat.type == "private":
    return await msg.reply_text(
        f"LIST HARGA BOT\n5K/MINGGU - 15K/BULAN\nPM {OWNER_USERNAME}"
    )

kb = [[InlineKeyboardButton("KONFIRMASI", callback_data="sewa")]]
await msg.reply_text("SEWA BOT AKTIF", reply_markup=InlineKeyboardMarkup(kb))

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE): q = update.callback_query await q.answer() if q.data == "sewa": await q.message.reply_text("KONFIRMASI SEWA DITERIMA")

================= TARGET =================

async def add(update, context): msg = update.message g = get_group(msg.chat.id)

if not msg.reply_to_message:
    return await msg.reply_text("REPLY USER DULU")

name = context.args[0].lower()
uid = str(msg.reply_to_message.from_user.id)

g["targets"][uid] = name
save_group(g)

await msg.reply_text(RESP["add"])

async def delete(update, context): msg = update.message g = get_group(msg.chat.id)

name = context.args[0].lower()

for uid, n in list(g["targets"].items()):
    if n == name:
        del g["targets"][uid]
        save_group(g)
        return await msg.reply_text(RESP["delete"])

await msg.reply_text("TIDAK DITEMUKAN")

async def listusn(update, context): g = get_group(update.message.chat.id) text = "LIST TARGET:\n\n" for uid, name in g["targets"].items(): text += f"{name} ({uid})\n" await update.message.reply_text(text)

================= USER =================

async def adduser(update, context): msg = update.message g = get_group(msg.chat.id)

uid = str(msg.reply_to_message.from_user.id)
name = context.args[0].lower()

g["allowed_users"][uid] = name
save_group(g)

await msg.reply_text(RESP["adduser"])

async def deluser(update, context): msg = update.message g = get_group(msg.chat.id)

name = context.args[0].lower()

for uid, n in list(g["allowed_users"].items()):
    if n == name:
        del g["allowed_users"][uid]
        g["targets"].pop(uid, None)
        g["premium_users"].pop(uid, None)
        save_group(g)
        return await msg.reply_text(RESP["deluser"])

await msg.reply_text("TIDAK DITEMUKAN")

async def listuser(update, context): g = get_group(update.message.chat.id) text = "LIST USER:\n\n" for uid, name in g["allowed_users"].items(): text += f"{name} ({uid})\n" await update.message.reply_text(text)

================= TEXT =================

async def addtext(update, context): g = get_group(update.message.chat.id) g["texts"].append(" ".join(context.args).lower()) save_group(g) await update.message.reply_text(RESP["addtext"])

async def deltext(update, context): g = get_group(update.message.chat.id) t = " ".join(context.args).lower() if t in g["texts"]: g["texts"].remove(t) save_group(g) return await update.message.reply_text(RESP["deltext"]) await update.message.reply_text("TIDAK ADA")

async def alltext(update, context): g = get_group(update.message.chat.id) text = "LIST TEXT:\n\n" for i, t in enumerate(g["texts"], 1): text += f"{i}. {t}\n" await update.message.reply_text(text)

================= DELETE PESAN =================

async def deletepesan(update, context): g = get_group(update.message.chat.id) mode = context.args[0].lower() g["delete_on"] = mode == "on" save_group(g) await update.message.reply_text(RESP["delete_on"] if g["delete_on"] else RESP["delete_off"])

================= FILTER =================

async def filtertext(update, context): g = get_group(update.message.chat.id) g["filter_text"] = context.args[0].lower() == "on" save_group(g) await update.message.reply_text("FILTER TEXT UPDATE")

async def filterfoto(update, context): g = get_group(update.message.chat.id) g["filter_foto"] = context.args[0].lower() == "on" save_group(g) await update.message.reply_text("FILTER FOTO UPDATE")

================= PREMIUM =================

async def listpremium(update, context): text = "LIST PREMIUM:\n\n" for g in groups_col.find(): for uid, d in g.get("premium_users", {}).items(): text += f"{d['name']} - {uid}\n" await update.message.reply_text(text)

async def cekmasaaktif(update, context): msg = update.message uid = str(msg.from_user.id)

for g in groups_col.find():
    clean = g.get("premium_users", {}).get(uid)
    if clean:
        if clean.get("expire") == -1:
            return await msg.reply_text(
                "👑 STATUS PREMIUM: SELAMANYA

" "KAMU USER VIP TANPA BATAS WAKTU 🔥" )

sisa = int((clean["expire"] - time.time()) / 86400)

        if sisa < 0:
            return await msg.reply_text("❌ PREMIUM SUDAH EXPIRED")

        return await msg.reply_text(
            f"👑 STATUS PREMIUM: AKTIF

" f"NAMA: {clean['name']} " f"SISA: {sisa} HARI " f"GRUP: {g['chat_id']}" )

await msg.reply_text("❌ KAMU TIDAK PREMIUM")

async def masaaktif(update, context): await update.message.reply_text("FITUR MASA AKTIF AKTIF")

================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("sewabot", sewabot)) app.add_handler(CommandHandler("infobot", infobot)) app.add_handler(CommandHandler("help", help_cmd))

app.add_handler(CommandHandler("add", add)) app.add_handler(CommandHandler("delete", delete)) app.add_handler(CommandHandler("listusn", listusn))

app.add_handler(CommandHandler("adduser", adduser)) app.add_handler(CommandHandler("deluser", deluser)) app.add_handler(CommandHandler("listuser", listuser))

app.add_handler(CommandHandler("addtext", addtext)) app.add_handler(CommandHandler("deltext", deltext)) app.add_handler(CommandHandler("alltext", alltext))

app.add_handler(CommandHandler("deletepesan", deletepesan)) app.add_handler(CommandHandler("filtertext", filtertext)) app.add_handler(CommandHandler("filterfoto", filterfoto))

app.add_handler(CommandHandler("listpremium", listpremium)) app.add_handler(CommandHandler("cekmasaaktif", cekmasaaktif)) app.add_handler(CommandHandler("masaaktif", masaaktif))

app.add_handler(CallbackQueryHandler(callback)) app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT RUNNING") app.run_polling(drop_pending_updates=True)
