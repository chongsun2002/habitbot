from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from .db.db import Database

class AddReflectionStates:
    START, ADD = range(2)

    pre_state_messages = {
        0: "",
        1: "Tell me more about what you learnt!",
    }

    end_message = "Thank you for sharing!"

async def start_add_reflection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_state = AddReflectionStates.ADD
    await update.message.reply_text(
        AddReflectionStates.pre_state_messages[next_state]
    )
    return next_state

# Should check if user is in the existing db
async def add_reflection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    Database.get_instance().update_reflection(user.id, text)
    await update.message.reply_text(AddReflectionStates.end_message)
    return ConversationHandler.END

add_reflection_handler = ConversationHandler(
    entry_points=[CommandHandler("add_reflection", start_add_reflection_command)],
    states={
        AddReflectionStates.ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reflection_command)],
    },
    fallbacks=[],
)
