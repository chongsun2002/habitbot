from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
from .db.db import Database
from datetime import timezone

class MessageScheduler:
    _instance = None  # Class variable to store the singleton instance

    def __init__(self):
        """Private constructor to prevent direct instantiation."""
        if MessageScheduler._instance is not None:
            raise Exception("This class is a singleton! Use get_instance() instead.")
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self._add_jobs()

    @classmethod
    def get_instance(cls):
        """Factory method to get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.start_scheduler()
        return cls._instance
    
    async def scheduled_reminder_messages(self):
        from .bot import TelegramBot
        message = "Good Evening! We hope your day has been great" \
        ":) Here's a friendly reminder to do your habit for today!"
        bot = await TelegramBot.get_instance()
        await bot.broadcast_message(message, Database.get_instance().get_users_streaks_breaking())

    async def scheduled_broken_streak_messages(self):
        from .bot import TelegramBot
        message = "Good Morning! We noticed you missed a few days of your habit :( " \
        "We hope you're coping fine with life :D If need be, you can always use /edit_habit to make your habit easier.\n\n" \
        "Have a great day ahead!"
        bot = await TelegramBot.get_instance()
        await bot.broadcast_message(message, Database.get_instance().get_users_streaks_broken())

    async def scheduled_reflection_sending(self):
        from .bot import TelegramBot
        bot = await TelegramBot.get_instance()
        db = Database.get_instance()
        user_ids = db.get_all_users()
        for user in user_ids:
            # Retrieve a random reflection from other users that have given consent.
            reflection = db.retrieve_random_reflection(user)
            if reflection:
                logging.info(f"Sending reflection to user {user}: {reflection}")
                await bot.send_message(user, reflection)
            else:
                logging.info(f"No available reflection for user {user}.")
            await asyncio.sleep(0.1)

    async def scheduled_message_test(self):
        from .bot import TelegramBot
        logging.info("Scheduled called")
        message = "Testing for scheduled messages"
        bot = await TelegramBot.get_instance()
        await bot.broadcast_message(message, Database.get_instance().get_all_users())

    def _add_jobs(self):
        """Add scheduled jobs for reminders and streak messages."""
        # Reminder Messages - Every day at 5 PM UTC+5
        self.scheduler.add_job(
            self.scheduled_reminder_messages,
            trigger=CronTrigger(hour=12, minute=0, timezone=timezone.utc)
        )

        # Broken Streak Messages - Every day at 5 AM UTC+5 (i.e. 00:00 UTC)
        self.scheduler.add_job(
            self.scheduled_broken_streak_messages,
            trigger=CronTrigger(hour=0, minute=0, timezone=timezone.utc)
        )

        # Reflection Messages - Every day at 9 PM UTC+5 (i.e. 16:00 UTC)
        self.scheduler.add_job(
            self.scheduled_reflection_sending,
            trigger=CronTrigger(hour=0, minute=0, timezone=timezone.utc)
        )

    def start_scheduler(self):
        """Starts the scheduler."""
        self.scheduler.start()
        logging.info("Message Scheduler is running!")

    def stop_scheduler(self):
        """Stops the scheduler."""
        self.scheduler.shutdown()
        logging.info("Message Scheduler stopped!")
