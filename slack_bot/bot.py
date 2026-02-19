"""Slack bot — M3ta'z A.I. 9 Labz.

Uses Slack Bolt with Socket Mode (no public URL needed).
Responds to:
  - Direct messages
  - @mentions in channels
  - /m3taz slash command

Channel → business context:
  #lotus / #business → lotus_group
  #eagle-eye         → eagle_eye
  #family            → family
  #meta / #metaos    → meta
  (default)          → personal
"""

from __future__ import annotations

import logging
import threading

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from orchestration.router import M3tazRouter, IncomingMessage

logger = logging.getLogger(__name__)

CHANNEL_CONTEXT_MAP = {
    "lotus": "lotus_group",
    "business": "lotus_group",
    "eagle": "eagle_eye",
    "family": "family",
    "meta": "meta",
    "metaos": "meta",
    "q3bi": "meta",
}


def _resolve_context(channel_name: str) -> str:
    name = (channel_name or "").lower()
    for key, ctx in CHANNEL_CONTEXT_MAP.items():
        if key in name:
            return ctx
    return "personal"


def _channel_name(app: App, channel_id: str) -> str:
    try:
        info = app.client.conversations_info(channel=channel_id)
        return info["channel"].get("name", "")
    except Exception:
        return ""


def create_slack_app(router: M3tazRouter) -> App:
    app = App(
        token=config.SLACK_BOT_TOKEN,
        signing_secret=config.SLACK_SIGNING_SECRET,
    )

    @app.event("app_mention")
    def handle_mention(event, say, client) -> None:
        text = event.get("text", "")
        # Strip the bot mention
        bot_id = client.auth_test()["user_id"]
        text = text.replace(f"<@{bot_id}>", "").strip()

        channel_id = event.get("channel", "")
        channel_name = _channel_name(app, channel_id)
        chat_context = _resolve_context(channel_name)
        user = event.get("user", "unknown")

        msg = IncomingMessage(
            platform="slack",
            user_id=user,
            username=user,
            chat_id=channel_id,
            text=text,
            chat_context=chat_context,
        )

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(router.route(msg))
        loop.close()

        say(result.text)

    @app.event("message")
    def handle_dm(event, say, client) -> None:
        # Only handle DMs (channel_type == "im")
        if event.get("channel_type") != "im":
            return
        if event.get("bot_id"):
            return

        text = event.get("text", "").strip()
        if not text:
            return

        user = event.get("user", "unknown")
        channel_id = event.get("channel", "")

        msg = IncomingMessage(
            platform="slack",
            user_id=user,
            username=user,
            chat_id=channel_id,
            text=text,
            chat_context="personal",
        )

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(router.route(msg))
        loop.close()

        say(result.text)

    @app.command("/m3taz")
    def handle_slash(ack, respond, command) -> None:
        ack()
        text = command.get("text", "").strip()
        channel_id = command.get("channel_id", "")
        channel_name = command.get("channel_name", "")
        user = command.get("user_id", "unknown")

        if not text:
            respond("What can I help you with? Try: `/m3taz research AI trends in 2026`")
            return

        chat_context = _resolve_context(channel_name)
        msg = IncomingMessage(
            platform="slack",
            user_id=user,
            username=user,
            chat_id=channel_id,
            text=text,
            chat_context=chat_context,
        )

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(router.route(msg))
        loop.close()

        respond(f"*Backend: {result.backend_used}*\n\n{result.text}")

    return app


def run_slack_bot() -> None:
    if not config.SLACK_BOT_TOKEN or not config.SLACK_APP_TOKEN:
        logger.warning("Slack tokens not configured — Slack bot will not start")
        return
    router = M3tazRouter()
    app = create_slack_app(router)
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    logger.info("Starting Slack bot (Socket Mode)...")
    handler.start()
