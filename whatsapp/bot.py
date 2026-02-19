"""WhatsApp bot — M3ta'z A.I. 9 Labz.

Uses the Meta WhatsApp Cloud API (webhook-based).
The FastAPI web app at webapp/app.py mounts these routes.

Webhook endpoints:
  GET  /webhooks/whatsapp  — verification challenge
  POST /webhooks/whatsapp  — incoming messages

Setup:
  1. Create a Meta Developer app at https://developers.facebook.com/apps
  2. Add WhatsApp Business product
  3. Set WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_VERIFY_TOKEN in .env
  4. Configure webhook URL: https://your-domain.com/webhooks/whatsapp
  5. Subscribe to: messages
"""

from __future__ import annotations

import logging

import httpx
from fastapi import Request, Response

import config
from orchestration.router import M3tazRouter, IncomingMessage

logger = logging.getLogger(__name__)

_router = M3tazRouter()

# Phone number prefix → business context
PHONE_CONTEXT_MAP: dict[str, str] = {
    # Add specific numbers here if needed
    # e.g. "+1555": "lotus_group"
}


def _resolve_context(phone: str) -> str:
    for prefix, ctx in PHONE_CONTEXT_MAP.items():
        if phone.startswith(prefix):
            return ctx
    return "personal"


async def whatsapp_verify(request: Request) -> Response:
    """Handle GET verification challenge from Meta."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


async def whatsapp_webhook(request: Request) -> Response:
    """Handle POST events from Meta WhatsApp Cloud API."""
    try:
        body = await request.json()
    except Exception:
        return Response(content="Bad Request", status_code=400)

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for raw_msg in messages:
            msg_type = raw_msg.get("type")
            if msg_type != "text":
                # Future: handle image, audio, document
                continue

            text = raw_msg.get("text", {}).get("body", "").strip()
            from_phone = raw_msg.get("from", "")
            msg_id = raw_msg.get("id", "")
            chat_context = _resolve_context(from_phone)

            msg = IncomingMessage(
                platform="whatsapp",
                user_id=from_phone,
                username=from_phone,
                chat_id=from_phone,
                text=text,
                chat_context=chat_context,
                raw=raw_msg,
            )
            result = await _router.route(msg)

            await send_whatsapp_message(from_phone, result.text)
    except Exception as exc:
        logger.error("WhatsApp webhook error: %s", exc)

    # Always return 200 to Meta
    return Response(content="OK", status_code=200)


async def send_whatsapp_message(to: str, text: str) -> None:
    """Send a text message via WhatsApp Cloud API."""
    if not config.WHATSAPP_TOKEN or not config.WHATSAPP_PHONE_ID:
        logger.warning("WhatsApp not configured — cannot send message")
        return

    url = f"https://graph.facebook.com/v19.0/{config.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},  # WhatsApp text limit
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if not resp.is_success:
            logger.error("WhatsApp send failed: %s %s", resp.status_code, resp.text)
