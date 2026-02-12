"""M3ta'z A.I. 9 Labz — Main entry point.

Runs both the Telegram bot and the web app concurrently.
For production, use docker-compose to run them as separate services.
"""

import asyncio
import logging
import threading

import uvicorn

from config import WEBAPP_HOST, WEBAPP_PORT
from telegram_bot.bot import run_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def start_webapp():
    """Start the FastAPI web app in a separate thread."""
    uvicorn.run(
        "webapp.app:app",
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        log_level="info",
    )


def main():
    logger.info("Starting M3ta'z A.I. 9 Labz...")
    logger.info(f"Web app will be available at http://{WEBAPP_HOST}:{WEBAPP_PORT}")

    # Start web app in background thread
    webapp_thread = threading.Thread(target=start_webapp, daemon=True)
    webapp_thread.start()

    # Run Telegram bot in main thread (blocking)
    run_bot()


if __name__ == "__main__":
    main()
