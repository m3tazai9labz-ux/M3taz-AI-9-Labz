"""Database models for M3ta'z A.I. 9 Labz content hub."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Telegram users and family members."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
    username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(50), default="member")  # admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    content_items = relationship("ContentItem", back_populates="submitted_by_user")


class ContentItem(Base):
    """Any piece of content ingested through Telegram or other sources."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id = Column(Integer, nullable=True)
    telegram_chat_id = Column(Integer, nullable=True)

    # Content metadata
    content_type = Column(String(50), nullable=False)  # photo, video, document, link, text, voice
    category = Column(String(50), default="uncategorized")
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)  # instagram, amazon, chatgpt, camera, etc.

    # Storage
    file_path = Column(String(1000), nullable=True)
    thumbnail_path = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # For links and text
    url = Column(String(2000), nullable=True)
    text_content = Column(Text, nullable=True)

    # Context
    chat_context = Column(String(50), default="personal")  # personal, lotus_group, family, meta
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_by_user = relationship("User", back_populates="content_items")

    # Tags and organization
    tags = Column(Text, nullable=True)  # comma-separated tags

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sharing
    is_shared = Column(Boolean, default=False)
    shared_with = Column(Text, nullable=True)  # comma-separated user IDs


class Collection(Base):
    """Named collections / albums for organizing content."""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    collection_type = Column(String(50), default="album")  # album, portfolio, project, archive
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("CollectionItem", back_populates="collection")


class CollectionItem(Base):
    """Junction table linking content to collections."""

    __tablename__ = "collection_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    sort_order = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow)

    collection = relationship("Collection", back_populates="items")
    content_item = relationship("ContentItem")


class ChatMapping(Base):
    """Maps Telegram chat IDs to conversation contexts."""

    __tablename__ = "chat_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id = Column(Integer, unique=True, nullable=False)
    chat_context = Column(String(50), nullable=False)  # personal, lotus_group, family, meta
    chat_title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
