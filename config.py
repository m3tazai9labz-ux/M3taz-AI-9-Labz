"""Central configuration for M3ta'z A.I. 9 Labz."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
MEDIA_STORE_PATH = Path(os.getenv("MEDIA_STORE_PATH", BASE_DIR / "media_store" / "uploads"))
THUMBNAIL_PATH = Path(os.getenv("THUMBNAIL_PATH", BASE_DIR / "media_store" / "thumbnails"))

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
]
ALLOWED_GROUP_IDS = [
    int(gid.strip())
    for gid in os.getenv("ALLOWED_GROUP_IDS", "").split(",")
    if gid.strip()
]

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'm3taz_hub.db'}")

# Web App
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8000"))
WEBAPP_SECRET_KEY = os.getenv("WEBAPP_SECRET_KEY", "change-me")

# Media
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# Content categories
CONTENT_CATEGORIES = [
    "research",       # ChatGPT articles, web research
    "photos",         # Personal/family photos
    "videos",         # Instagram reels, recordings
    "shopping",       # Amazon, product links
    "documents",      # PDFs, docs, files
    "notes",          # Text messages, voice transcripts
    "links",          # Bookmarks, saved URLs
    "social_media",   # Instagram, TikTok, etc.
    "family",         # Family-specific content
    "business",       # Lotus Group, business items
    "meta_os",        # MetaOS / Q3bi related
    "uncategorized",
]

# Conversation contexts (Telegram chats mapped to purposes)
CHAT_CONTEXTS = {
    "personal": "Personal conversations and notes",
    "lotus_group": "Lotus Group business discussions",
    "family": "Family collaboration and sharing",
    "meta": "Meta / MetaOS / Q3bi development",
}
