from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from .db.db import Database

class CompletionStates:
    START, QUESTION = range(2)

    pre_state_messages = {
        0: "",
        1: "Have you done the habit today?"
    }

    end_message_success = "Great Job! Keep going at it :)"
    end_message_failure = "It's okay! You still got it, don't stop trying :)"

# Should check if user is in the existing db
async def completed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    next_state = CompletionStates.QUESTION
    reply_keyboard = [["I'm done!", "I'm not done :("]]
    await update.message.reply_text(
        "Are you done with your habit for today?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder=CompletionStates.pre_state_messages[next_state]
        ),
    )
    return next_state

async def question_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    if text == "I'm done!":
        Database.get_instance().update_streak_if_not_today(user.id)
        await update.message.reply_text(CompletionStates.end_message_success)
    else:
        await update.message.reply_text(CompletionStates.end_message_failure)

    return ConversationHandler.END

completion_handler = ConversationHandler(
    entry_points=[CommandHandler("complete", completed_command)],
    states={
        CompletionStates.QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_command)],
    },
    fallbacks=[],
)
