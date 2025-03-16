from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import os
from utils import is_telegram_ip
from bot.bot import TelegramBot
import asyncio
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

telegram_bot = None

async def lifespan(app: FastAPI):
    global telegram_bot
    telegram_bot = await TelegramBot.get_instance()
    await telegram_bot.set_webhook()
    yield
    # requests.get(f"{TELEGRAM_API}/deleteWebhook")


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    client_ip = request.client.host

    if not is_telegram_ip(client_ip):
        raise HTTPException(status_code=403, detail="Forbidden: Only ip addresses in telegram's subnet are allowed to access this route.")
    update_json = await request.json()
    logging.info("Webhook triggered")
    asyncio.create_task(telegram_bot.process_update(update_json))
    return { "status": "ok" }


DATABASE_FILE = "internal_proj.db" 

@app.get("/download_db")
async def download_db():
    """
    Returns the current database file as a downloadable attachment.
    """
    if not os.path.exists(DATABASE_FILE):
        raise HTTPException(status_code=404, detail="Database file not found.")
    
    return FileResponse(
        path=DATABASE_FILE,
        filename="internal_proj.db",
        media_type="application/octet-stream"
    )