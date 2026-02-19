"""M3ta'z Kub3 — Central Message Router.

Receives a normalized IncomingMessage from any platform adapter,
classifies intent, selects the right AI backend, dispatches, and
returns a plain-text response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from orchestration.intent_classifier import IntentClassifier, Intent
from orchestration.business_router import BusinessRouter

logger = logging.getLogger(__name__)


@dataclass
class IncomingMessage:
    """Normalized message from any platform."""

    platform: str          # "telegram" | "discord" | "slack" | "whatsapp"
    user_id: str           # Platform-specific user identifier
    username: str          # Display name
    chat_id: str           # Channel / chat identifier
    text: str              # Message text (empty string if no text)
    chat_context: str = "personal"   # personal | lotus_group | family | meta | eagle_eye
    attachments: list[dict] = field(default_factory=list)  # {type, url/path}
    raw: Optional[dict] = None       # Original platform payload


@dataclass
class OutgoingMessage:
    """Response to send back to the originating platform."""

    text: str
    intent: str = ""
    backend_used: str = ""
    error: bool = False


class M3tazRouter:
    """Central router — classify → route → respond."""

    def __init__(self) -> None:
        self._classifier = IntentClassifier()
        self._business_router = BusinessRouter()

    async def route(self, msg: IncomingMessage) -> OutgoingMessage:
        """Main entry point. Takes a normalized message and returns a response."""
        logger.info(
            "Routing message from %s/%s in context=%s: %.80s",
            msg.platform, msg.username, msg.chat_context, msg.text,
        )

        # 1 — Classify intent
        try:
            intent, topic = await self._classifier.classify(msg.text, msg.chat_context)
        except Exception as exc:
            logger.error("Intent classification failed: %s", exc)
            intent, topic = Intent.CHAT, ""

        logger.info("Intent=%s topic=%s", intent, topic)

        # 2 — Content ingestion (photos, files, voice) handled by platform layer
        if intent == Intent.CONTENT_INGEST:
            return OutgoingMessage(
                text="Content saved! Use /search to find it later.",
                intent=intent,
                backend_used="content_handler",
            )

        # 3 — Route to AI backend
        try:
            response_text, backend = await self._business_router.dispatch(
                intent=intent,
                topic=topic,
                message=msg,
            )
            return OutgoingMessage(
                text=response_text,
                intent=intent,
                backend_used=backend,
            )
        except Exception as exc:
            logger.error("Dispatch failed (intent=%s): %s", intent, exc)
            return OutgoingMessage(
                text="Something went wrong on my end. Please try again.",
                intent=intent,
                error=True,
            )
