"""Lark bot — M3ta'z A.I. 9 Labz.

Handles inbound events from the Lark Open Platform via HTTP webhooks.
The FastAPI app at webapp/app.py mounts these handlers.

Webhook endpoints:
  GET/POST  /webhooks/lark  — challenge verification + event dispatch

Event types handled:
  im.message.receive_v1        — new chat message (route to AI hub)
  contact.user.updated_v3      — contact record changed
  application.bot.menu_v6      — bot menu button clicked

Setup (see integrations_sop.md §8 for full guide):
  1. Create a Lark app at https://open.larksuite.com/app
  2. Enable: Bot, Im, Bitable (Base), Drive, Wiki permissions
  3. Subscribe to events: im.message.receive_v1
  4. Set webhook URL: https://your-domain.com/webhooks/lark
  5. Copy App ID, App Secret, Verification Token, Encrypt Key → .env
"""

from __future__ import annotations

import json
import logging

from fastapi import Request, Response

import config
from integrations.lark import LarkClient
from orchestration.router import IncomingMessage, M3tazRouter

logger = logging.getLogger(__name__)

_router = M3tazRouter()
_lark = LarkClient()

# Lark chat/open_id → business context
# Fill in actual open_id values from your Lark workspace once deployed
CHAT_CONTEXT_MAP: dict[str, str] = {
    # "oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx": "eagle_eye",   # Eagle Eye Lark group
    # "oc_yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy": "lotus_group", # Lotus Group Lark group
}


def _resolve_context(chat_id: str, sender_open_id: str) -> str:
    return CHAT_CONTEXT_MAP.get(chat_id, CHAT_CONTEXT_MAP.get(sender_open_id, "eagle_eye"))


async def lark_webhook(request: Request) -> Response:
    """Unified Lark webhook handler (challenge + events)."""
    try:
        raw_body = await request.body()
        body = json.loads(raw_body)
    except Exception:
        return Response(content="Bad Request", status_code=400)

    # ── URL verification challenge (sent when you first configure the webhook)
    if "challenge" in body:
        challenge = body["challenge"]
        logger.info("Lark: responding to URL verification challenge")
        return Response(
            content=json.dumps({"challenge": challenge}),
            media_type="application/json",
        )

    # ── Signature verification (optional but strongly recommended)
    ts = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")
    sig = request.headers.get("X-Lark-Signature", "")
    if sig and not _lark.verify_webhook_signature(ts, nonce, raw_body, sig):
        logger.warning("Lark: webhook signature mismatch — rejected")
        return Response(content="Forbidden", status_code=403)

    # ── Route event by type
    header = body.get("header", {})
    event_type = header.get("event_type", "")
    event = body.get("event", {})

    logger.info("Lark event: %s", event_type)

    try:
        if event_type == "im.message.receive_v1":
            await _handle_message(event)
        elif event_type in ("contact.user.updated_v3", "contact.user.created_v3"):
            await _handle_contact_event(event_type, event)
        elif event_type == "application.bot.menu_v6":
            await _handle_menu_click(event)
        else:
            logger.debug("Lark: unhandled event type '%s'", event_type)
    except Exception as exc:
        logger.error("Lark webhook processing error: %s", exc)

    # Lark requires 200 within 3 seconds
    return Response(content=json.dumps({"code": 0}), media_type="application/json")


async def _handle_message(event: dict) -> None:
    """Route an inbound Lark chat message through the M3taz hub."""
    msg = event.get("message", {})
    sender = event.get("sender", {})

    msg_type = msg.get("message_type", "")
    message_id = msg.get("message_id", "")
    chat_id = msg.get("chat_id", "")
    sender_id = sender.get("sender_id", {}).get("open_id", "")
    sender_name = sender.get("sender_type", "user")

    # Lark message content is JSON-encoded in msg.content
    if msg_type != "text":
        logger.debug("Lark: ignoring non-text message type '%s'", msg_type)
        return

    try:
        content = json.loads(msg.get("content", "{}"))
        text = content.get("text", "").strip()
    except Exception:
        return

    if not text:
        return

    chat_context = _resolve_context(chat_id, sender_id)

    incoming = IncomingMessage(
        platform="lark",
        user_id=sender_id,
        username=sender_name,
        chat_id=chat_id,
        text=text,
        chat_context=chat_context,
        raw=event,
    )

    result = await _router.route(incoming)

    # Reply in the same Lark thread
    if message_id:
        await _lark.reply_message(message_id, result.text)
    elif sender_id:
        await _lark.send_message(sender_id, result.text, receive_id_type="open_id")


async def _handle_contact_event(event_type: str, event: dict) -> None:
    """Log Lark contact create/update events (hook into GHL sync if needed)."""
    user_id = event.get("object", {}).get("open_id", "unknown")
    logger.info("Lark contact event: %s — user %s", event_type, user_id)
    # Future: sync Lark contact changes to GoHighLevel CRM


async def _handle_menu_click(event: dict) -> None:
    """Handle bot menu button clicks (quick-action buttons in Lark)."""
    operator = event.get("operator", {})
    event_key = event.get("event_key", "")
    open_id = operator.get("operator_id", {}).get("open_id", "")

    logger.info("Lark: menu click key='%s' from %s", event_key, open_id)

    # Map menu event keys to quick commands
    responses: dict[str, str] = {
        "crm_status":    "Checking your GoHighLevel pipeline...",
        "daily_brief":   "Preparing your daily brief...",
        "eagle_eye_kb":  "Searching Eagle Eye knowledge base...",
    }

    reply = responses.get(event_key, f"Menu action '{event_key}' received.")
    if open_id:
        await _lark.send_message(open_id, reply, receive_id_type="open_id")
