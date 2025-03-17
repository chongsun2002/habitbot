import sqlite3
from sqlite3 import Error
from typing import Tuple, Optional
from random import choice
from datetime import datetime, timedelta, UTC, timezone
from .db_utils import streak_to_points
import logging

DATABASE_NAME = "internal_proj.db"

class Database:
    _instance = None  # Class variable to store the singleton instance

    def __init__(self):
        """Private constructor to prevent direct instantiation."""
        if Database._instance is not None:
            raise Exception("This class is a singleton! Use get_instance() instead.")

        self.con = self.get_db_connection()
        self.cursor = self.con.cursor() if self.con else None

    @classmethod
    def get_instance(cls):
        """Factory method to get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.create_users_table()
            cls._instance.create_challenges_table()
            cls._instance.create_info_table()
            cls._instance.create_reflections_table()  # <-- Added this line
        return cls._instance
    
    @staticmethod
    def get_db_connection():
        """Establish and return a connection to the SQLite database."""
        try:
            con = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
            con.row_factory = sqlite3.Row
            return con
        except Error as e:
            print(f"Database Connection Error: {e}")
            return None


    def close(self):
        """Closes the database connection."""
        if self.con:
            self.con.close()

    def create_users_table(self):
        """Creates the Users table if it does not exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                Telegram TEXT PRIMARY KEY,
                TelegramHandle TEXT,
                Habit TEXT,
                Location TEXT,
                TimePeriod TEXT,
                ReflectionConsent INTEGER,
                lastDoneDate TEXT,
                Streak TEXT,
                Points INTEGER,
                Category TEXT
            )
        """)
        self.con.commit()

    def create_reflections_table(self):
        """Creates the Reflections table to store multiple reflections per user."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Telegram TEXT,
                Reflection TEXT,
                CreatedAt TEXT,
                FOREIGN KEY (Telegram) REFERENCES Users(Telegram)
            )
        """)
        self.con.commit()

    def create_challenges_table(self):
        """Creates the WeeklyChallenges table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS WeeklyChallenges (
                Category TEXT PRIMARY KEY,
                Challenge1 TEXT,
                Challenge2 TEXT,
                Challenge3 TEXT
            )
        """)
        self.con.commit()

    def create_info_table(self):
        """Creates the Information table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Information (
                Date INTEGER PRIMARY KEY,
                Content TEXT
            )
        """)
        self.con.commit()

    def add_new_user(self, user: Tuple[str, str, str, str, str, int, str, str, int, str]):
        """
        Inserts a new user into the Users table without a Reflection field.
        
        Args:
            user: A tuple containing:
                - Telegram (str)
                - TelegramHandle (str)
                - Habit (str)
                - Location (str)
                - TimePeriod (str)
                - ReflectionConsent (int)
                - lastDoneDate (str) in "YYYY-MM-DD" format (or NULL if not set)
                - Streak (str)
                - Points (int)
                - Category (str)
        """
        self.cursor.execute("""
            INSERT INTO Users 
            (Telegram, TelegramHandle, Habit, Location, TimePeriod, ReflectionConsent, lastDoneDate, Streak, Points, Category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user)
        self.con.commit()

    def update_reflection(self, telegram: str, reflection: str):
        from datetime import datetime, timedelta, timezone
        # Get current time in UTC+5
        now_utc5 = datetime.now(timezone.utc) + timedelta(hours=5)
        created_at_str = now_utc5.strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute("""
            INSERT INTO Reflections (Telegram, Reflection, CreatedAt)
            VALUES (?, ?, ?)
        """, (telegram, reflection, created_at_str))
        self.con.commit()

    
    def update_habit(self, telegram: str, habit, location, time_period):
        if habit:
            self.cursor.execute(f"UPDATE Users SET Habit = ? WHERE Telegram = ?", (habit, telegram))
            self.con.commit()
        if location:
            self.cursor.execute(f"UPDATE Users SET Location = ? WHERE Telegram = ?", (location, telegram))
            self.con.commit()
        if time_period:
            self.cursor.execute(f"UPDATE Users SET TimePeriod = ? WHERE Telegram = ?", (time_period, telegram))
            self.con.commit()

    def retrieve_random_reflection(self, telegram: str) -> Optional[str]:
        """
        Retrieves a random reflection from users (other than the specified Telegram)
        that have granted reflection consent (ReflectionConsent = 1).
        """
        # This query joins Reflections and Users so we only select reflections
        # where the user has ReflectionConsent = 1 and is not the given telegram.
        query = """
            SELECT r.Reflection
            FROM Reflections r
            JOIN Users u ON r.Telegram = u.Telegram
            WHERE r.Telegram != ? AND u.ReflectionConsent = 1
        """
        self.cursor.execute(query, (telegram,))
        data = self.cursor.fetchall()
        if not data:
            return None
        from random import choice
        return choice([row["Reflection"] for row in data])

    def update_last_done_date(self, telegram: str, last_done_date: int):
        """Updates the last done date for a user."""
        self.cursor.execute("UPDATE Users SET lastDoneDate = ? WHERE Telegram = ?", (last_done_date, telegram))
        self.con.commit()
    
    def retrieve_last_done_date(self, telegram: str) -> Optional[int]:
        """Retrieves a user's last done date."""
        self.cursor.execute("SELECT lastDoneDate FROM Users WHERE Telegram = ?", (telegram,))
        result = self.cursor.fetchone()
        return result["lastDoneDate"] if result else None

    def retrieve_streak(self, telegram: str) -> Optional[str]:
        self.cursor.execute("SELECT * FROM Users WHERE Telegram = ?", (telegram,))
        user_data = self.cursor.fetchone()

        if user_data:
            logging.info(f"📋 Retrieved User Data: {dict(user_data)}")
            return user_data["Streak"] if user_data["Streak"] else "0"
        
        logging.warning(f"⚠️ No user found for Telegram ID: {telegram}")
        return None
    
    def is_user_registered(self, telegram: str) -> bool:
        """Checks if a user exists in the Users table."""
        self.cursor.execute("SELECT 1 FROM Users WHERE Telegram = ?", (telegram,))
        result = self.cursor.fetchone()

        if result:
            return True
        else:
            return False
    
    def update_streak_if_not_today(self, telegram: str):
        """
        Checks if the user's last done date (in UTC+5) is today.
        If not, increments the user's streak by 1 and updates lastDoneDate to today's date.
        
        This ensures that each day's challenge is only counted once.
        """
        # Get current date adjusted to UTC+5
        current_date = (datetime.now(UTC) + timedelta(hours=5)).date()
        current_date_str = current_date.isoformat()  # "YYYY-MM-DD"

        # Retrieve the user's last done date (assumed to be stored as "YYYY-MM-DD")
        last_done_date = self.retrieve_last_done_date(telegram)
        
        # If the last done date is already today, do nothing.
        if last_done_date == current_date_str:
            return

        # Otherwise, retrieve and increment the user's streak.
        current_streak_str = self.retrieve_streak(telegram)
        new_streak = current_streak_str + "1"
        self.update_points(telegram, streak_to_points(new_streak))

        # Update the user's streak and last done date in the database.
        self.cursor.execute("UPDATE Users SET Streak = ? WHERE Telegram = ?", (str(new_streak), telegram))
        self.cursor.execute("UPDATE Users SET lastDoneDate = ? WHERE Telegram = ?", (current_date_str, telegram))
        self.con.commit()
    
    def is_streak_broken(self, telegram):
        year, month, date = self.retrieve_last_done_date(telegram).split("-")
        last_date = datetime(int(year), int(month), int(date), tzinfo=timezone(timedelta(hours=5)))
        now = datetime.now(UTC) + timedelta(hours=5)
        if last_date <= now - timedelta(days=2):
            return True
        else:
            return False
        
    def get_leaderboard(self):
        """
        Retrieves a leaderboard sorted by points in descending order.
        Returns:
            A list of sqlite3.Row objects with 'TelegramHandle' and 'Points'.
        """
        self.cursor.execute("SELECT TelegramHandle, Points FROM Users ORDER BY Points DESC LIMIT 10")
        return self.cursor.fetchall()

    def update_points(self, telegram: str, points: int):
        """Updates the user's points."""
        self.cursor.execute("UPDATE Users SET Points = ? WHERE Telegram = ?", (points, telegram))
        self.con.commit()

    def retrieve_points(self, telegram: str) -> Optional[int]:
        """Retrieves a user's points."""
        self.cursor.execute("SELECT Points FROM Users WHERE Telegram = ?", (telegram,))
        result = self.cursor.fetchone()
        return result["Points"] if result else None

    def add_new_weekly_challenge(self, weeklychallenge: Tuple[str, str, str, str]):
        """Adds a new weekly challenge."""
        self.cursor.execute("INSERT INTO WeeklyChallenges VALUES (?, ?, ?, ?)", weeklychallenge)
        self.con.commit()
    
    def retrieve_challenge(self, category: str, challenge_number: int) -> Optional[str]:
        """Retrieves a specific challenge from WeeklyChallenges."""
        challenge_column = f"Challenge{challenge_number}"
        self.cursor.execute(f"SELECT {challenge_column} FROM WeeklyChallenges WHERE Category = ?", (category,))
        result = self.cursor.fetchone()
        return result[challenge_column] if result else None
    
    def add_new_information(self, info: Tuple[int, str]):
        """Adds new informational content."""
        self.cursor.execute("INSERT INTO Information VALUES (?, ?)", info)
        self.con.commit()
    
    def retrieve_information(self, date: int) -> Optional[str]:
        """Retrieves informational content based on date."""
        self.cursor.execute("SELECT Content FROM Information WHERE Date = ?", (date,))
        result = self.cursor.fetchone()
        return result["Content"] if result else None
    
    def update_all_streaks(self):
        """
        Updates the streak for all users based on their last done date.
        
        The logic assumes:
        - The current time is adjusted to UTC+5 (as in your other methods).
        - If a user's last done date equals yesterday's date (in UTC+5),
            the streak is incremented.
        - Otherwise, the streak is reset to "0".
        
        This function should be run once daily (e.g., at 3 AM).
        """
        # Get current time in UTC+5 and determine yesterday's date.
        current_datetime = datetime.now(UTC) + timedelta(hours=5)
        yesterday = (current_datetime - timedelta(days=1)).date()
        
        # Retrieve all users.
        self.cursor.execute("SELECT Telegram, lastDoneDate, Streak FROM Users")
        users = self.cursor.fetchall()
        
        for user in users:
            telegram = user["Telegram"]
            last_done_date_str = user["lastDoneDate"]
            new_streak = None
            if last_done_date_str:
                try:
                    last_done_date = datetime.strptime(last_done_date_str, "%Y-%m-%d").date()
                except ValueError:
                    # If parsing fails, reset the streak.
                    new_streak = "0"
                else:
                    if last_done_date == yesterday:
                        # Increment streak if yesterday's challenge was completed.
                        continue
                    else:
                        new_streak = user["Streak"] + "0"
            else:
                # No recorded challenge date; treat as streak broken.
                new_streak = "0"
            
            self.cursor.execute(
                "UPDATE Users SET Streak = ? WHERE Telegram = ?",
                (str(new_streak), telegram)
            )
        self.con.commit()

    def get_all_users(self):
        self.cursor.execute(
            "SELECT Telegram FROM Users"
        )
        return [row["Telegram"] for row in self.cursor.fetchall()]

    def get_users_streaks_breaking(self):
        """
        Retrieves a list of Telegram IDs for users whose last done date is not today.
        
        This includes users with no recorded last done date (NULL)
        or whose date does not match today's date (in UTC+5).
        
        Returns:
            A list of Telegram IDs (strings) to remind for challenge completion.
        """
        current_datetime = datetime.now(timezone.utc) + timedelta(hours=5)
        today_str = current_datetime.date().isoformat()         # "YYYY-MM-DD"
        yesterday_str = (current_datetime - timedelta(days=1)).date().isoformat()  # "YYYY-MM-DD"

        # Use SQLite's date() function for proper date comparisons.
        self.cursor.execute(
            """
            SELECT Telegram FROM Users
            WHERE lastDoneDate IS NULL OR lastDoneDate NOT IN (?, ?)
            """,
            (today_str, yesterday_str)
        )

        return [row["Telegram"] for row in self.cursor.fetchall()]

    
    def get_users_streaks_broken(self):
        """
        Retrieves a list of Telegram IDs for users whose last done date is more than 2 days ago.
        
        Users are included if:
        - They have no recorded last done date (NULL).
        - Their last done date is **before** (today - 2 days) in UTC+5.

        Returns:
            A list of Telegram IDs (strings) whose streaks are broken.
        """
        current_datetime = datetime.now(timezone.utc) + timedelta(hours=5)  # Convert to UTC+5
        today_str = current_datetime.date().isoformat()         # "YYYY-MM-DD"
        two_days_ago_str = (current_datetime - timedelta(days=2)).date().isoformat()  # Format: "YYYY-MM-DD"
        yesterday_str = (current_datetime - timedelta(days=1)).date().isoformat()  # "YYYY-MM-DD"
        # Use the date() function to force proper date comparisons.
        self.cursor.execute(
            """
            SELECT Telegram FROM Users
            WHERE lastDoneDate IS NULL OR lastDoneDate NOT IN (?, ?, ?)
            """,
            (two_days_ago_str, yesterday_str, today_str)
        )
        
        return [row["Telegram"] for row in self.cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        if self.con:
            self.con.close()
