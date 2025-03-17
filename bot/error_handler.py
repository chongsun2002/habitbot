from telegram.ext import (
    ContextTypes
)
import logging

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler to catch all exceptions during update processing."""
    logging.error("Exception occurred while handling an update:", exc_info=context.error)
    
    if update and hasattr(update, "message") and update.message:
        try:
            await update.message.reply_text("Oops! Something went wrong. Please try again later.")
        except Exception as e:
            logging.error("Failed to send error message to user: %s", e)