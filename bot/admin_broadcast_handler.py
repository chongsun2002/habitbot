from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
from .config import Config

class AdminBroadcastStates:
    START, AUTH, GET = range(3)

    pre_state_messages = {
        0: "",
        1: "Enter the password to broadcast:",
        2: "Type the message you want to broadcast:",
    }

    wrong_pw_message = "Incorrect password!"
    end_message = "Your request has been sent!"

async def start_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_state = AdminBroadcastStates.AUTH
    await update.message.reply_text(
        AdminBroadcastStates.pre_state_messages[next_state]
    )
    return next_state

# Should check if user is in the existing db
async def enter_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    if text != Config.ADMIN_PW:
        await update.message.reply_text(AdminBroadcastStates.wrong_pw_message)
        return ConversationHandler.END
    else:
        next_state = AdminBroadcastStates.GET
        await update.message.reply_text(AdminBroadcastStates.pre_state_messages[next_state])
        return next_state


# Should check if user is in the existing db
async def get_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .bot import TelegramBot
    user = update.message.from_user
    text = update.message.text
    bot = await TelegramBot().get_instance()
    await bot.broadcast_message(text)
    await update.message.reply_text(AdminBroadcastStates.end_message)
    return ConversationHandler.END



admin_broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler("admin_broadcast", start_broadcast_command)],
    states={
        AdminBroadcastStates.AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password_command)],
        AdminBroadcastStates.GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message_command)],
    },
    fallbacks=[],
)
