from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
from .db.db import Database

def format_streak(streak: str) -> str:
    """
    Removes the first element from the streak string and maps the remaining
    0s and 1s to emojis for a nicer display.
    
    Args:
        streak (str): A string representing the user's streak, e.g. "1010110"
    
    Returns:
        str: A formatted string with emojis.
    """
    if not streak or len(streak) < 2:
        return ""
    
    # Remove the first character
    streak = streak[1:]
    
    # Define the mapping for each character
    emoji_mapping = {
        '1': '🔥',  # successful day
        '0': '❌'   # missed day
    }
    
    # Build the formatted streak
    streak_message = "Each 🔥 emoji represents a day where you completed the habit, and each ❌ is a missed day. \n\n"
    formatted = streak_message + "".join(emoji_mapping.get(ch, ch) for ch in streak)
    return formatted


async def get_streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    streak = Database.get_instance().retrieve_streak(user.id)
    streak = format_streak(streak)
    if streak == "" or not streak:
        streak = "You currently don't have an ongoing streak!"
    await update.message.reply_text(streak)
    return ConversationHandler.END

get_streak_handler = ConversationHandler(
    entry_points=[CommandHandler("get_streak", get_streak_command)],
    states={},
    fallbacks=[],
)
