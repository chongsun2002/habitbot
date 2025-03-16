import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8080))
    ADMIN_PW = os.getenv("ADMIN_PW")
    