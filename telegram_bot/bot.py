"""Main Telegram bot application — registers handlers and runs polling."""

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from database.engine import init_db
from telegram_bot.handlers import (
    cmd_categories,
    cmd_collections,
    cmd_help,
    cmd_newcollection,
    cmd_search,
    cmd_setchat,
    cmd_share,
    cmd_start,
    cmd_status,
    cmd_tag,
)
from telegram_bot.ingest import (
    handle_document,
    handle_photo,
    handle_text,
    handle_video,
    handle_voice,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_app():
    """Build and configure the Telegram bot application."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN not set. "
            "Copy .env.example to .env and add your bot token from @BotFather."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("tag", cmd_tag))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("setchat", cmd_setchat))
    app.add_handler(CommandHandler("collections", cmd_collections))
    app.add_handler(CommandHandler("newcollection", cmd_newcollection))
    app.add_handler(CommandHandler("share", cmd_share))

    # Content ingestion handlers (order matters — more specific first)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


async def on_startup(app):
    """Initialize database on startup."""
    await init_db()
    logger.info("Database initialized.")


def run_bot():
    """Run the Telegram bot with polling."""
    app = build_app()
    app.post_init = on_startup
    logger.info("Starting M3ta'z A.I. 9 Labz Telegram Bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
