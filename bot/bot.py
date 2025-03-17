import logging
import asyncio
from .config import Config
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application
)
from .onboarding_handler import onboarding_handler
from .completion_handler import completion_handler
from .reflection_handler import add_reflection_handler
from .help_handler import help_handler
from .leaderboard_handler import leaderboard_handler
from .start_handler import start_handler
from .admin_broadcast_handler import admin_broadcast_handler
from .edit_habit_handler import edit_habit_handler
from .get_streak_handler import get_streak_handler

from .db.db import Database
from .message_scheduler import MessageScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

class TelegramBot:
    _instance = None

    def __init__(self):
        self.app = Application.builder().token(Config.TOKEN).build()
        self.database = Database()
        Database.get_db_connection()
        self.message_scheduler = MessageScheduler.get_instance()

    async def _init_async(self):
        # Asynchronous initialization call
        await self.app.initialize()

    @classmethod
    async def get_instance(cls):
        # Return the singleton instance, initializing it if necessary.
        if cls._instance is None:
            instance = cls()
            await instance._init_async()  # Await asynchronous initialization
            instance._add_handlers()
            cls._instance = instance
        return cls._instance
        

    def _add_handlers(self):
        self.app.add_handler(onboarding_handler)
        self.app.add_handler(completion_handler)
        self.app.add_handler(add_reflection_handler)
        self.app.add_handler(help_handler)
        self.app.add_handler(leaderboard_handler)
        self.app.add_handler(start_handler)
        self.app.add_handler(edit_habit_handler)
        self.app.add_handler(admin_broadcast_handler)
        self.app.add_handler(get_streak_handler)

    async def set_webhook(self):
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        await self.app.bot.set_webhook(webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")

    async def process_update(self, update: dict):
        update_obj = Update.de_json(update, self.app.bot)
        await self.app.process_update(update_obj)

    async def send_message(self, user_id: int, text: str):
        """
        Sends a message to a single user.

        Args:
            user_id (int): Telegram user ID to send the message to.
            text (str): The message to be sent.
        """
        try:
            await self.app.bot.send_message(chat_id=user_id, text=text)
            logging.info(f"📩 Message sent to user {user_id}")
        except TelegramError as e:
            logging.warning(f"⚠️ Failed to send message to {user_id}: {e}")

    async def broadcast_message(self, text: str, user_ids=None):
        """
        Sends a message to all users in the database while preventing Telegram rate limits.
        """
        if user_ids is None:
            logging.warning("Getting all users as user_ids are empty")
            user_ids = Database.get_instance().get_all_users()  # Fetch users from DB

        if not user_ids:
            logging.warning("⚠️ No users found in the database.")
            return
        
        success_count = 0
        failure_count = 0

        for i, user_id in enumerate(user_ids):
            try:
                await self.send_message(user_id, text)
                success_count += 1
                logging.info(f"Sent to user {user_id}")

                if (i + 1) % 29 == 0:  # ✅ Pause after every 29 messages
                    await asyncio.sleep(1)  # ✅ Wait for 1 second before sending more

            except TelegramError as e:
                failure_count += 1
                logging.warning(f"⚠️ Failed to send message to {user_id}: {e}")

            await asyncio.sleep(0.1)  # Delay 100ms between messages

        logging.info(f"✅ Broadcast completed: {success_count} sent, {failure_count} failed.")