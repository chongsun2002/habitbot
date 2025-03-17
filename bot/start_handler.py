from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import logging

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_message = start_message = (
        "Welcome to Little Big Habits ⭐! Here are all the commands you will need for this challenge:\n\n"
        "/onboard - Register your details (what habit you are building, consent to share your reflection with others anonymously)\n"
        "/complete - Log your habit completion for the day\n"
        "/get_streak - View your habit progress\n"
        "/leaderboard - View the current leaderboard\n"
        "/add_reflection - Insert your reflection entry. You will be prompted to reflect on Days 5, 8, 11.\n"
        "/edit_habit - Modify your habit\n"
        "/help - View all available functions"
    )
    await update.message.reply_text(start_message)
    return ConversationHandler.END



start_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={},
    fallbacks=[],
)
