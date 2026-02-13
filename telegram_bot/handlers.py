"""Telegram bot command and message handlers."""

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    ALLOWED_GROUP_IDS,
    ALLOWED_USER_IDS,
    CONTENT_CATEGORIES,
    MEDIA_STORE_PATH,
    THUMBNAIL_PATH,
)
from database.engine import async_session
from database.models import ChatMapping, Collection, ContentItem, User

logger = logging.getLogger(__name__)


def is_authorized(update: Update) -> bool:
    """Check if the user/chat is authorized."""
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None

    # If no allowlists configured, allow all (dev mode)
    if not ALLOWED_USER_IDS and not ALLOWED_GROUP_IDS:
        return True

    if user_id and user_id in ALLOWED_USER_IDS:
        return True
    if chat_id and chat_id in ALLOWED_GROUP_IDS:
        return True

    return False


async def _get_or_create_user(telegram_user) -> int:
    """Get or create a user record, return user DB id."""
    async with async_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.telegram_id == telegram_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                display_name=telegram_user.full_name or telegram_user.username or "Unknown",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user.id


async def _get_chat_context(chat_id: int) -> str:
    """Look up the chat context for a given Telegram chat ID."""
    async with async_session() as session:
        from sqlalchemy import select

        stmt = select(ChatMapping).where(ChatMapping.telegram_chat_id == chat_id)
        result = await session.execute(stmt)
        mapping = result.scalar_one_or_none()
        return mapping.chat_context if mapping else "personal"


async def _save_content(
    content_type: str,
    update: Update,
    file_path: str | None = None,
    thumbnail_path: str | None = None,
    file_size: int | None = None,
    mime_type: str | None = None,
    url: str | None = None,
    text_content: str | None = None,
    source: str | None = None,
    category: str = "uncategorized",
) -> ContentItem:
    """Save a content item to the database."""
    user_id = await _get_or_create_user(update.effective_user)
    chat_context = await _get_chat_context(update.effective_chat.id)

    async with async_session() as session:
        item = ContentItem(
            telegram_message_id=update.message.message_id if update.message else None,
            telegram_chat_id=update.effective_chat.id,
            content_type=content_type,
            category=category,
            source=source,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            file_size_bytes=file_size,
            mime_type=mime_type,
            url=url,
            text_content=text_content,
            chat_context=chat_context,
            submitted_by=user_id,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


# ── Command Handlers ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not is_authorized(update):
        await update.message.reply_text("Not authorized.")
        return

    await update.message.reply_text(
        "Welcome to M3ta'z A.I. 9 Labz Hub\n\n"
        "Send me anything — photos, videos, links, documents, voice messages, "
        "or just text — and I'll organize and store it for you.\n\n"
        "Commands:\n"
        "/start — This message\n"
        "/status — Storage stats\n"
        "/search <query> — Search your content\n"
        "/categories — List content categories\n"
        "/tag <category> — Tag the last item\n"
        "/collections — List your collections\n"
        "/newcollection <name> — Create a collection\n"
        "/setchat <context> — Set this chat's context\n"
        "/share <item_id> — Share an item with family\n"
        "/help — Full help"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show storage statistics."""
    if not is_authorized(update):
        return

    async with async_session() as session:
        from sqlalchemy import func, select

        # Count items by type
        stmt = select(
            ContentItem.content_type,
            func.count(ContentItem.id),
        ).group_by(ContentItem.content_type)
        result = await session.execute(stmt)
        counts = result.all()

        total = sum(c for _, c in counts)
        breakdown = "\n".join(f"  {t}: {c}" for t, c in counts) if counts else "  (none yet)"

        # Count collections
        coll_count = await session.scalar(select(func.count(Collection.id)))

        await update.message.reply_text(
            f"M3ta'z Hub — Storage Status\n\n"
            f"Total items: {total}\n"
            f"Collections: {coll_count}\n\n"
            f"By type:\n{breakdown}"
        )


async def cmd_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List available content categories."""
    if not is_authorized(update):
        return

    cats = "\n".join(f"  - {c}" for c in CONTENT_CATEGORIES)
    await update.message.reply_text(
        f"Content Categories:\n\n{cats}\n\n"
        "Use /tag <category> to tag the last saved item."
    )


async def cmd_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag the most recent content item with a category."""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /tag <category>")
        return

    category = context.args[0].lower()
    if category not in CONTENT_CATEGORIES:
        await update.message.reply_text(
            f"Unknown category '{category}'. Use /categories to see options."
        )
        return

    async with async_session() as session:
        from sqlalchemy import select

        user_id = await _get_or_create_user(update.effective_user)
        stmt = (
            select(ContentItem)
            .where(ContentItem.submitted_by == user_id)
            .order_by(ContentItem.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            await update.message.reply_text("No items found to tag.")
            return

        item.category = category
        await session.commit()
        await update.message.reply_text(f"Tagged item #{item.id} as '{category}'.")


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search content by text."""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /search <query>")
        return

    query = " ".join(context.args)

    async with async_session() as session:
        from sqlalchemy import or_, select

        stmt = (
            select(ContentItem)
            .where(
                or_(
                    ContentItem.text_content.ilike(f"%{query}%"),
                    ContentItem.title.ilike(f"%{query}%"),
                    ContentItem.description.ilike(f"%{query}%"),
                    ContentItem.tags.ilike(f"%{query}%"),
                    ContentItem.source.ilike(f"%{query}%"),
                )
            )
            .order_by(ContentItem.created_at.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

        if not items:
            await update.message.reply_text(f"No results for '{query}'.")
            return

        lines = []
        for item in items:
            preview = (item.text_content or item.title or item.url or item.file_path or "")[:60]
            lines.append(f"#{item.id} [{item.content_type}/{item.category}] {preview}")

        await update.message.reply_text(
            f"Search results for '{query}':\n\n" + "\n".join(lines)
        )


async def cmd_setchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the context for the current chat."""
    if not is_authorized(update):
        return

    valid_contexts = ["personal", "lotus_group", "family", "meta"]
    if not context.args or context.args[0].lower() not in valid_contexts:
        await update.message.reply_text(
            f"Usage: /setchat <context>\n\nValid contexts: {', '.join(valid_contexts)}"
        )
        return

    chat_context = context.args[0].lower()
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or update.effective_chat.full_name or "DM"

    async with async_session() as session:
        from sqlalchemy import select

        stmt = select(ChatMapping).where(ChatMapping.telegram_chat_id == chat_id)
        result = await session.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            mapping.chat_context = chat_context
            mapping.chat_title = chat_title
        else:
            mapping = ChatMapping(
                telegram_chat_id=chat_id,
                chat_context=chat_context,
                chat_title=chat_title,
            )
            session.add(mapping)

        await session.commit()

    await update.message.reply_text(
        f"This chat is now mapped to context: '{chat_context}'"
    )


async def cmd_collections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all collections."""
    if not is_authorized(update):
        return

    async with async_session() as session:
        from sqlalchemy import func, select

        stmt = select(Collection).order_by(Collection.created_at.desc())
        result = await session.execute(stmt)
        collections = result.scalars().all()

        if not collections:
            await update.message.reply_text(
                "No collections yet. Create one with /newcollection <name>"
            )
            return

        lines = []
        for coll in collections:
            count_stmt = select(func.count()).where(
                __import__("database.models", fromlist=["CollectionItem"])
                .CollectionItem.collection_id == coll.id
            )
            lines.append(
                f"#{coll.id} {coll.name} ({coll.collection_type})"
                + (" [shared]" if coll.is_shared else "")
            )

        await update.message.reply_text("Collections:\n\n" + "\n".join(lines))


async def cmd_newcollection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new collection."""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /newcollection <name>")
        return

    name = " ".join(context.args)
    user_id = await _get_or_create_user(update.effective_user)

    async with async_session() as session:
        coll = Collection(name=name, created_by=user_id)
        session.add(coll)
        await session.commit()
        await session.refresh(coll)

    await update.message.reply_text(
        f"Collection '{name}' created (#{coll.id}). "
        "Forward or send content, then use /addto <collection_id> to add items."
    )


async def cmd_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Share a content item with family."""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /share <item_id>")
        return

    try:
        item_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Item ID must be a number.")
        return

    async with async_session() as session:
        from sqlalchemy import select

        stmt = select(ContentItem).where(ContentItem.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            await update.message.reply_text(f"Item #{item_id} not found.")
            return

        item.is_shared = True
        await session.commit()

    await update.message.reply_text(
        f"Item #{item_id} is now shared. Family members can view it in the web app."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full help message."""
    if not is_authorized(update):
        return

    await update.message.reply_text(
        "M3ta'z A.I. 9 Labz — Content Hub\n\n"
        "Just send me content and I'll store & organize it:\n"
        "  - Photos (from camera, Instagram, screenshots)\n"
        "  - Videos (reels, recordings)\n"
        "  - Documents (PDFs, files)\n"
        "  - Links (Amazon, articles, research)\n"
        "  - Text messages and notes\n"
        "  - Voice messages\n"
        "  - Forwarded messages from any chat\n\n"
        "Commands:\n"
        "  /start — Welcome message\n"
        "  /status — Storage statistics\n"
        "  /search <query> — Search content\n"
        "  /categories — List categories\n"
        "  /tag <category> — Tag last saved item\n"
        "  /collections — List collections\n"
        "  /newcollection <name> — Create collection\n"
        "  /setchat <context> — Set chat context\n"
        "    (personal, lotus_group, family, meta)\n"
        "  /share <item_id> — Share with family\n"
        "  /help — This message\n\n"
        "Web App: Check your .env for the web app URL\n"
        "to browse, search, and share your content library."
    )
