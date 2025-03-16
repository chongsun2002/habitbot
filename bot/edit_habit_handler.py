from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from .db.db import Database

class EditHabitStates:
    START, EDIT = range(2)

    pre_state_messages = {
        0: "",
        1: "Tell us what you would like to change your habit to:",
    }

    end_message = "Got it! Keep going at it!"

async def start_edit_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_state = EditHabitStates.EDIT
    await update.message.reply_text(
        EditHabitStates.pre_state_messages[next_state]
    )
    return next_state

# Should check if user is in the existing db
async def edit_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    Database.get_instance().update_habit(user.id, text, None, None)
    await update.message.reply_text(EditHabitStates.end_message)
    return ConversationHandler.END



edit_habit_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_habit", start_edit_habit_command)],
    states={
        EditHabitStates.EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_habit_command)],
    },
    fallbacks=[],
)
