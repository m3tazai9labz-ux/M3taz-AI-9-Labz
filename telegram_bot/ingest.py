"""Content ingestion handlers — processes all incoming Telegram media and text."""

import logging
import re
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import MAX_FILE_SIZE_MB, MEDIA_STORE_PATH, THUMBNAIL_PATH
from telegram_bot.handlers import _save_content, is_authorized

logger = logging.getLogger(__name__)

# Ensure storage directories exist
MEDIA_STORE_PATH.mkdir(parents=True, exist_ok=True)
THUMBNAIL_PATH.mkdir(parents=True, exist_ok=True)

# URL patterns for auto-categorization
SOURCE_PATTERNS = {
    r"amazon\.(com|co\.\w+)": ("shopping", "amazon"),
    r"instagram\.com": ("social_media", "instagram"),
    r"tiktok\.com": ("social_media", "tiktok"),
    r"youtube\.com|youtu\.be": ("social_media", "youtube"),
    r"chat\.openai\.com|chatgpt\.com": ("research", "chatgpt"),
    r"claude\.ai": ("research", "claude"),
    r"reddit\.com": ("research", "reddit"),
    r"twitter\.com|x\.com": ("social_media", "twitter"),
    r"facebook\.com|fb\.com": ("social_media", "facebook"),
    r"pinterest\.com": ("social_media", "pinterest"),
    r"medium\.com": ("research", "medium"),
    r"github\.com": ("research", "github"),
}


def _detect_source(text: str) -> tuple[str, str | None]:
    """Auto-detect category and source from URL or text content."""
    if not text:
        return "uncategorized", None

    for pattern, (category, source) in SOURCE_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return category, source

    # Check if it's a URL at all
    if re.search(r"https?://", text):
        return "links", "web"

    return "uncategorized", None


async def _download_file(file_obj, subfolder: str, filename: str) -> tuple[str, int]:
    """Download a Telegram file to local storage. Returns (path, size)."""
    dest_dir = MEDIA_STORE_PATH / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    tg_file = await file_obj.get_file()
    await tg_file.download_to_drive(str(dest_path))

    size = dest_path.stat().st_size
    return str(dest_path), size


# ── Message Handlers ─────────────────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos."""
    if not is_authorized(update):
        return

    photo = update.message.photo[-1]  # Largest size
    caption = update.message.caption or ""
    category, source = _detect_source(caption)
    if category == "uncategorized":
        category = "photos"

    filename = f"photo_{update.message.message_id}_{photo.file_unique_id}.jpg"
    file_path, file_size = await _download_file(photo, "photos", filename)

    item = await _save_content(
        content_type="photo",
        update=update,
        file_path=file_path,
        file_size=file_size,
        mime_type="image/jpeg",
        text_content=caption if caption else None,
        source=source,
        category=category,
    )

    await update.message.reply_text(
        f"Photo saved (#{item.id}) [{item.category}]"
        + (f"\n{caption[:100]}" if caption else "")
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming videos."""
    if not is_authorized(update):
        return

    video = update.message.video
    if video.file_size and video.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"Video too large (max {MAX_FILE_SIZE_MB}MB). Try compressing it first."
        )
        return

    caption = update.message.caption or ""
    category, source = _detect_source(caption)
    if category == "uncategorized":
        category = "videos"

    ext = video.mime_type.split("/")[-1] if video.mime_type else "mp4"
    filename = f"video_{update.message.message_id}_{video.file_unique_id}.{ext}"
    file_path, file_size = await _download_file(video, "videos", filename)

    item = await _save_content(
        content_type="video",
        update=update,
        file_path=file_path,
        file_size=file_size,
        mime_type=video.mime_type,
        text_content=caption if caption else None,
        source=source,
        category=category,
    )

    await update.message.reply_text(
        f"Video saved (#{item.id}) [{item.category}]"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming documents (PDFs, files, etc.)."""
    if not is_authorized(update):
        return

    doc = update.message.document
    if doc.file_size and doc.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"File too large (max {MAX_FILE_SIZE_MB}MB)."
        )
        return

    caption = update.message.caption or ""
    filename = doc.file_name or f"doc_{update.message.message_id}"
    file_path, file_size = await _download_file(doc, "documents", filename)

    item = await _save_content(
        content_type="document",
        update=update,
        file_path=file_path,
        file_size=file_size,
        mime_type=doc.mime_type,
        title=doc.file_name,
        text_content=caption if caption else None,
        category="documents",
    )

    await update.message.reply_text(
        f"Document saved (#{item.id}): {doc.file_name}"
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages."""
    if not is_authorized(update):
        return

    voice = update.message.voice
    filename = f"voice_{update.message.message_id}.ogg"
    file_path, file_size = await _download_file(voice, "voice", filename)

    item = await _save_content(
        content_type="voice",
        update=update,
        file_path=file_path,
        file_size=file_size,
        mime_type="audio/ogg",
        category="notes",
    )

    await update.message.reply_text(
        f"Voice message saved (#{item.id}). Duration: {voice.duration}s"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages — notes, links, research snippets."""
    if not is_authorized(update):
        return

    text = update.message.text
    if not text:
        return

    category, source = _detect_source(text)

    # Extract URLs
    url = None
    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        url = url_match.group(0)

    content_type = "link" if url else "text"

    item = await _save_content(
        content_type=content_type,
        update=update,
        url=url,
        text_content=text,
        source=source,
        category=category,
    )

    type_label = "Link" if url else "Note"
    await update.message.reply_text(
        f"{type_label} saved (#{item.id}) [{item.category}]"
    )


async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forwarded messages — preserve original context."""
    if not is_authorized(update):
        return

    msg = update.message
    forward_from = msg.forward_from.full_name if msg.forward_from else "Unknown"
    forward_info = f"[Forwarded from {forward_from}] "

    # Delegate to the appropriate handler based on content type
    if msg.photo:
        await handle_photo(update, context)
    elif msg.video:
        await handle_video(update, context)
    elif msg.document:
        await handle_document(update, context)
    elif msg.voice:
        await handle_voice(update, context)
    elif msg.text:
        await handle_text(update, context)
