from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = 'To get started, use the /onboard command.\n' \
    '/complete - to log your habit completion for the day \n' \
    '/add_reflection - to add a reflection for the day \n' \
    '/get_streak - to see you habit progress \n' \
    '/edit_habit - to modify your habit \n' \
    '/leaderboard - to view the current leaderboard \n' \
    ''
    await update.message.reply_text(help_message)
    return ConversationHandler.END



help_handler = ConversationHandler(
    entry_points=[CommandHandler("help", help_command)],
    states={},
    fallbacks=[],
)
