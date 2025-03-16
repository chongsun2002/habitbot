from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import logging

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_message = 'To get started, use the /onboard command.\n' \
    '/complete - to log your habit completion for the day \n' \
    '/add_reflection - to add a reflection for the day \n' \
    '/leaderboard - to view the current leaderboard'
    await update.message.reply_text(start_message)
    return ConversationHandler.END



start_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={},
    fallbacks=[],
)
