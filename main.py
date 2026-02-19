"""M3ta'z A.I. 9 Labz — Main entry point.

Starts all services concurrently:
  - FastAPI web app + WhatsApp webhook (port 8000)
  - Telegram bot (polling)
  - Discord bot (gateway)
  - Slack bot (Socket Mode)

For production, use docker-compose to run them as separate scaled services.
"""

import logging
import threading

import uvicorn

from config import (
    DISCORD_BOT_TOKEN,
    SLACK_BOT_TOKEN,
    SLACK_APP_TOKEN,
    TELEGRAM_BOT_TOKEN,
    WEBAPP_HOST,
    WEBAPP_PORT,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _start_webapp() -> None:
    """FastAPI: web dashboard + WhatsApp webhook."""
    uvicorn.run(
        "webapp.app:app",
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        log_level="info",
    )


def _start_discord() -> None:
    """Discord bot (blocking — runs its own event loop)."""
    if not DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set — Discord bot skipped")
        return
    from discord_bot.bot import run_discord_bot
    run_discord_bot()


def _start_slack() -> None:
    """Slack bot via Socket Mode (blocking)."""
    if not (SLACK_BOT_TOKEN and SLACK_APP_TOKEN):
        logger.warning("Slack tokens not set — Slack bot skipped")
        return
    from slack_bot.bot import run_slack_bot
    run_slack_bot()


def main() -> None:
    logger.info("Starting M3ta'z A.I. 9 Labz...")
    logger.info("  Web dashboard + WhatsApp webhook → http://%s:%s", WEBAPP_HOST, WEBAPP_PORT)
    logger.info("  Telegram: %s", "enabled" if TELEGRAM_BOT_TOKEN else "DISABLED (no token)")
    logger.info("  Discord:  %s", "enabled" if DISCORD_BOT_TOKEN else "DISABLED (no token)")
    logger.info("  Slack:    %s", "enabled" if (SLACK_BOT_TOKEN and SLACK_APP_TOKEN) else "DISABLED")

    # Start web app in background thread (also hosts WhatsApp webhooks)
    threading.Thread(target=_start_webapp, daemon=True, name="webapp").start()

    # Start Discord in background thread
    threading.Thread(target=_start_discord, daemon=True, name="discord").start()

    # Start Slack in background thread
    threading.Thread(target=_start_slack, daemon=True, name="slack").start()

    # Telegram bot runs in the main thread (blocking, keeps process alive)
    if TELEGRAM_BOT_TOKEN:
        from telegram_bot.bot import run_bot
        run_bot()
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — keeping process alive without Telegram")
        import time
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
