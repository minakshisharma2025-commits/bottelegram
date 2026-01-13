import nest_asyncio
nest_asyncio.apply()
import os
import subprocess
import aiofiles
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8530781378:AAET7A6tm7R9C8ToQYBl8-jjtu0L2KaI13E"
USER_BOTS_DIR = "user_bots"
pending_module_users = set()
admin_ids = {7899148519}

if not os.path.exists(USER_BOTS_DIR):
    os.makedirs(USER_BOTS_DIR)

def get_status(pid_file):
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = f.read().strip()
        return os.system(f"ps -p {pid} > /dev/null") == 0
    return False

async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

async def show_main_menu(update_or_query, context):
    buttons = [
        [InlineKeyboardButton("⬆️ Upload Bot", callback_data="upload")],
        [InlineKeyboardButton("▶️ Start Bot", callback_data="startbot"), InlineKeyboardButton("⏹ Stop Bot", callback_data="stopbot")],
        [InlineKeyboardButton("🪛 Module Installer", callback_data="modules")],
        [InlineKeyboardButton("🗑 Delete Bot", callback_data="delete")],
        [InlineKeyboardButton("📜 Show Logs", callback_data="logs")],
        [InlineKeyboardButton("🔍 Bot Status", callback_data="status")]
    ]

    if (update_or_query.effective_user.id if hasattr(update_or_query, 'effective_user') else update_or_query.from_user.id) in admin_ids:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin")])

    markup = InlineKeyboardMarkup(buttons)
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text("**Welcome to ChxHost Bot Panel** 🧠\n\nSelect an action below:", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update_or_query.edit_message_text("**Welcome to ChxHost Bot Panel** 🧠\n\nSelect an action below:", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    os.makedirs(os.path.join(USER_BOTS_DIR, user_id), exist_ok=True)
    await show_main_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_path = os.path.join(USER_BOTS_DIR, user_id)
    bot_path = os.path.join(user_path, "bot.py")
    pid_path = os.path.join(user_path, "pid.txt")
    log_path = os.path.join(user_path, "log.txt")

    if query.data == "startbot":
        files = os.listdir(user_path)
        file_buttons = [InlineKeyboardButton(f"📄 {file}", callback_data=f"start_{file}") for file in files if file.endswith(".py")]
        if file_buttons:
            markup = InlineKeyboardMarkup([[btn] for btn in file_buttons])
            await query.edit_message_text("Choose a bot file to start:", reply_markup=markup)
        else:
            await query.edit_message_text("❌ No bot files found to start.")
    
    elif query.data.startswith("start_"):
        filename = query.data.split("_", 1)[1]
        file_path = os.path.join(user_path, filename)
        if os.path.exists(file_path):
            proc = subprocess.Popen(["python3", filename], cwd=user_path,
                                    stdout=open(log_path, "w"), stderr=subprocess.STDOUT)
            with open(pid_path, "w") as f:
                f.write(str(proc.pid))
            await query.edit_message_text(f"**Starting bot `{filename}`...**\n\n✅ Bot started.", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(f"❌ File `{filename}` not found.")
    
    elif query.data == "stopbot":
        files = os.listdir(user_path)
        file_buttons = [InlineKeyboardButton(f"📄 {file}", callback_data=f"stop_{file}") for file in files if file.endswith(".py")]
        if file_buttons:
            markup = InlineKeyboardMarkup([[btn] for btn in file_buttons])
            await query.edit_message_text("Choose a bot file to stop:", reply_markup=markup)
        else:
            await query.edit_message_text("❌ No running bot files to stop.")

    elif query.data.startswith("stop_"):
        filename = query.data.split("_", 1)[1]
        file_path = os.path.join(user_path, filename)
        if os.path.exists(pid_path):
            with open(pid_path, "r") as f:
                pid = f.read().strip()
            try:
                os.kill(int(pid), 9)
                os.remove(pid_path)
                await query.edit_message_text(f"**Stopping bot `{filename}`...**\n\n⛔ Bot stopped.", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await query.edit_message_text(f"❌ Error stopping bot `{filename}`: {e}")
        else:
            await query.edit_message_text(f"⚠️ No bot process running for `{filename}`.")

    elif query.data == "delete":
        files = os.listdir(user_path)
        file_buttons = [InlineKeyboardButton(f"📄 {file}", callback_data=f"delete_{file}") for file in files]
        if file_buttons:
            markup = InlineKeyboardMarkup([[btn] for btn in file_buttons])
            await query.edit_message_text("Choose a bot file to delete:", reply_markup=markup)
        else:
            await query.edit_message_text("❌ No bot files found to delete.")
    
    elif query.data.startswith("delete_"):
        filename = query.data.split("_", 1)[1]
        file_path = os.path.join(user_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            await query.edit_message_text(f"🗑 File `{filename}` deleted.")
        else:
            await query.edit_message_text(f"❌ File `{filename}` not found.")
    
    elif query.data == "logs":
        if os.path.exists(log_path):
            await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(log_path), filename="log.txt")
            await query.edit_message_text("📜 Logs sent.", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text("⚠ No logs found.")
        await query.edit_message_text("🔙 Back to menu:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

    elif query.data == "status":
        if os.path.exists(pid_path):
            with open(pid_path, "r") as f:
                pid = f.read().strip()
            running = os.system(f"ps -p {pid} > /dev/null") == 0
            status = "✅ Running" if running else "⛔ Not Running"
        else:
            status = "⚠️ No PID found"
        await query.edit_message_text(f"**Bot Status:** `{status}`", parse_mode=ParseMode.MARKDOWN)
        await query.edit_message_text("🔙 Back to menu:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

    elif query.data == "upload":
        await query.edit_message_text("Send your `.py`, `.txt`, or other bot file.", parse_mode=ParseMode.MARKDOWN)

    elif query.data == "modules":
        module_buttons = [
            [InlineKeyboardButton("📦 Available Modules", callback_data="available_modules")],
            [InlineKeyboardButton("➕ Install Module", callback_data="install_module")],
            [InlineKeyboardButton("📄 Upload requirements.txt", callback_data="upload")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.edit_message_text("**Module Installer:**", reply_markup=InlineKeyboardMarkup(module_buttons), parse_mode=ParseMode.MARKDOWN)

    elif query.data == "main_menu":
        await show_main_menu(query, context)

    elif query.data == "admin":
        await context.bot.send_message(chat_id=query.message.chat_id, text="⚙️ Admin panel features coming soon...")

async def doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing(update, context)
    user_id = str(update.effective_user.id)
    user_path = os.path.join(USER_BOTS_DIR, user_id)
    file = update.message.document
    file_path = os.path.join(user_path, file.file_name)

    msg = await update.message.reply_text("Uploading...", parse_mode=ParseMode.MARKDOWN)
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)

    await msg.edit_text(f"✅ `{file.file_name}` uploaded.", parse_mode=ParseMode.MARKDOWN)

    if "requirements.txt" in file.file_name:
        installing = await update.message.reply_text("📦 Installing from requirements.txt...")
        result = subprocess.getoutput(f"pip install -r {file_path}")
        await installing.edit_text(f"```{result}```", parse_mode=ParseMode.MARKDOWN)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in pending_module_users:
        pending_module_users.remove(user_id)
        msg = await update.message.reply_text("📦 Installing module...")
        result = subprocess.getoutput(f"pip install {update.message.text}")
        await msg.edit_text(f"```{result}```", parse_mode=ParseMode.MARKDOWN)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
