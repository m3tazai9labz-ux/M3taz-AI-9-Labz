"""GoHighLevel (GHL) webhook handler — M3ta'z A.I. 9 Labz.

Receives real-time events from GoHighLevel and triggers AI workflows.
The FastAPI app at webapp/app.py mounts this handler.

Webhook endpoint:
  POST  /webhooks/gohighlevel

GHL sends JSON events for:
  ContactCreate / ContactUpdate / ContactDelete
  OpportunityCreate / OpportunityUpdate / OpportunityStatusChange
  InboundMessage  (incoming SMS/email into GHL conversations)
  ConversationUnreadUpdate
  NoteCreate / TaskCreate

Setup:
  1. In GHL → Settings → Integrations → Webhooks → Add webhook
  2. URL: https://your-domain.com/webhooks/gohighlevel
  3. Select event types (ContactCreate, OpportunityStatusChange, InboundMessage, etc.)
  4. (Optional) Set GHL_WEBHOOK_SECRET in .env for signature verification
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import Request, Response

import config
from integrations.gohighlevel import GHLClient
from orchestration.router import IncomingMessage, M3tazRouter

logger = logging.getLogger(__name__)

_router = M3tazRouter()
_ghl = GHLClient()


def _verify_ghl_signature(body: bytes, signature: str) -> bool:
    """Verify GHL webhook HMAC-SHA256 signature if secret is configured."""
    secret = config.GHL_WEBHOOK_SECRET
    if not secret:
        return True  # skip if not configured
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.lstrip("sha256="))


async def ghl_webhook(request: Request) -> Response:
    """Receive and dispatch GoHighLevel webhook events."""
    raw_body = await request.body()

    # Verify signature if header present
    sig = request.headers.get("x-ghl-signature", "")
    if sig and not _verify_ghl_signature(raw_body, sig):
        logger.warning("GHL: webhook signature mismatch — rejected")
        return Response(content="Forbidden", status_code=403)

    try:
        body = json.loads(raw_body)
    except Exception:
        return Response(content="Bad Request", status_code=400)

    event_type = body.get("type", "")
    logger.info("GHL webhook: %s", event_type)

    try:
        if event_type in ("ContactCreate", "ContactUpdate"):
            await _handle_contact_event(event_type, body)
        elif event_type in ("OpportunityCreate", "OpportunityUpdate", "OpportunityStatusChange"):
            await _handle_opportunity_event(event_type, body)
        elif event_type == "InboundMessage":
            await _handle_inbound_message(body)
        elif event_type == "ConversationUnreadUpdate":
            await _handle_unread_conversation(body)
        elif event_type in ("NoteCreate", "TaskCreate"):
            await _handle_note_or_task(event_type, body)
        else:
            logger.debug("GHL: unhandled event type '%s'", event_type)
    except Exception as exc:
        logger.error("GHL webhook error (event=%s): %s", event_type, exc)

    return Response(content="OK", status_code=200)


async def _handle_contact_event(event_type: str, data: dict) -> None:
    """Process new or updated GHL contact — log and optionally notify."""
    name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()
    email = data.get("email", "")
    phone = data.get("phone", "")
    tags = data.get("tags", [])

    action = "created" if event_type == "ContactCreate" else "updated"
    logger.info(
        "GHL contact %s: %s (%s / %s) tags=%s",
        action, name, email, phone, tags,
    )
    # Future: push summary to Lark group, Telegram, or AnythingLLM doc store


async def _handle_opportunity_event(event_type: str, data: dict) -> None:
    """Process pipeline opportunity events — alert when stages change."""
    opp_name = data.get("name", "Unknown opportunity")
    stage = data.get("pipelineStage", {}).get("name", "?")
    status = data.get("status", "")
    value = data.get("monetaryValue", 0)
    contact_name = data.get("contactName", "")

    logger.info(
        "GHL opportunity %s: '%s' → stage='%s' status='%s' value=$%.0f contact='%s'",
        event_type, opp_name, stage, status, value, contact_name,
    )

    # Build a natural-language summary and route to AI hub for follow-up suggestions
    if event_type == "OpportunityStatusChange":
        summary = (
            f"[GHL CRM] Opportunity '{opp_name}' for {contact_name} "
            f"moved to stage '{stage}' (status: {status}, value: ${value:,.0f}). "
            "What's the recommended next action?"
        )
        msg = IncomingMessage(
            platform="ghl_webhook",
            user_id="ghl_system",
            username="GoHighLevel",
            chat_id="ghl_crm",
            text=summary,
            chat_context="eagle_eye",
            raw=data,
        )
        result = await _router.route(msg)
        logger.info("GHL opportunity AI response: %.120s", result.text)
        # Future: send result.text to a Telegram/Lark notification channel


async def _handle_inbound_message(data: dict) -> None:
    """Route an inbound SMS/email from GHL to the AI hub and auto-reply."""
    body_text = data.get("body", "").strip()
    contact_id = data.get("contactId", "")
    conversation_id = data.get("conversationId", "")
    channel = data.get("type", "SMS")

    if not body_text:
        return

    logger.info(
        "GHL inbound %s from contact %s: %.80s", channel, contact_id, body_text
    )

    msg = IncomingMessage(
        platform=f"ghl_{channel.lower()}",
        user_id=contact_id,
        username=data.get("contactName", contact_id),
        chat_id=conversation_id,
        text=body_text,
        chat_context="eagle_eye",
        raw=data,
    )

    result = await _router.route(msg)

    # Auto-reply via GHL SMS if enabled
    if config.GHL_AUTO_REPLY_SMS and channel == "SMS" and contact_id:
        await _ghl.send_sms(contact_id, result.text)
        logger.info("GHL: auto-replied to %s via SMS", contact_id)


async def _handle_unread_conversation(data: dict) -> None:
    """Log unread conversation updates (for dashboard alerting)."""
    count = data.get("unreadCount", 0)
    location = data.get("locationId", "")
    logger.info("GHL: %d unread conversation(s) in location %s", count, location)


async def _handle_note_or_task(event_type: str, data: dict) -> None:
    """Log new notes and tasks created in GHL."""
    logger.info(
        "GHL %s: contact=%s body=%.80s",
        event_type,
        data.get("contactId", "?"),
        data.get("body", data.get("title", "")),
    )
