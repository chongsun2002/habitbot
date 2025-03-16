from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from .db.db import Database

def format_leaderboard_message(leaderboard_entries):
    """
    Formats leaderboard entries into a message string suitable for Telegram.
    
    Args:
        leaderboard_entries: A list of sqlite3.Row objects with 'Telegram' and 'Points'.
    
    Returns:
        A string representing the formatted leaderboard message.
    """
    if not leaderboard_entries:
        return "No leaderboard entries available."

    # Start with a header.
    message = "🏆 Leaderboard 🏆\n\n"
    
    current_rank = 0
    previous_points = None

    for index, row in enumerate(leaderboard_entries, start=1):
        telegram = row["TelegramHandle"]
        points = row["Points"]

        # If points are the same as previous entry, maintain rank
        if points != previous_points:
            current_rank = index  # Update rank only if points are different

        message += f"{current_rank}. @{telegram} - {points} point(s)\n"
        previous_points = points  # Update the last seen points

    return message

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaderboard = Database.get_instance().get_leaderboard()
    await update.message.reply_text(format_leaderboard_message(leaderboard))
    return ConversationHandler.END



leaderboard_handler = ConversationHandler(
    entry_points=[CommandHandler("leaderboard", leaderboard_command)],
    states={},
    fallbacks=[],
)
