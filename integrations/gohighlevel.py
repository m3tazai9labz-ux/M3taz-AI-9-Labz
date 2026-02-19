"""GoHighLevel (GHL) integration — CRM, pipeline, and conversation client.

GoHighLevel is used as the primary CRM and marketing automation platform for
Eagle Eye Vision Labz and Lotus Group. We integrate with the GHL v2 API to:
  - Manage contacts and leads
  - Sync pipeline opportunities (stage changes, new deals)
  - Send and receive SMS/conversation messages via GHL
  - Receive real-time webhook events (new lead, stage change, inbound SMS)

API Docs: https://highlevel.stoplight.io/docs/integrations/
API Base: https://services.leadconnectorhq.com

Auth: Bearer token — either your Agency API key (simple) or OAuth 2.0 (recommended).
      Set GHL_API_KEY in .env for Agency API key auth.
      Location ID is required for all sub-account (location) level requests.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

_BASE = "https://services.leadconnectorhq.com"
_VERSION_HEADER = {"Version": "2021-07-28"}  # required by GHL v2 API


class GHLClient:
    """Client for the GoHighLevel v2 REST API."""

    API_KEY = config.GHL_API_KEY
    LOCATION_ID = config.GHL_LOCATION_ID

    def _headers(self) -> dict:
        h = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
        }
        h.update(_VERSION_HEADER)
        return h

    # ── Contacts ──────────────────────────────────────────────────────

    async def search_contacts(
        self,
        query: str = "",
        limit: int = 20,
        skip: int = 0,
    ) -> list[dict]:
        """Search contacts in the GHL location."""
        params: dict[str, Any] = {
            "locationId": self.LOCATION_ID,
            "limit": limit,
            "skip": skip,
        }
        if query:
            params["query"] = query

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/contacts/",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()

        data = resp.json()
        return data.get("contacts", [])

    async def get_contact(self, contact_id: str) -> dict:
        """Get a single contact by ID."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/contacts/{contact_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
        return resp.json().get("contact", {})

    async def create_contact(self, data: dict) -> dict:
        """Create a new contact.

        Minimum required: {"firstName": ..., "email": ...} or {"phone": ...}
        Optional: lastName, name, email, phone, address1, city, state, country,
                  postalCode, companyName, tags, source, customField
        """
        payload = {"locationId": self.LOCATION_ID, **data}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/contacts/",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        result = resp.json().get("contact", {})
        logger.info("GHL: created contact %s (%s)", result.get("id"), data.get("email"))
        return result

    async def update_contact(self, contact_id: str, data: dict) -> dict:
        """Update an existing contact's fields."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.put(
                f"{_BASE}/contacts/{contact_id}",
                headers=self._headers(),
                json=data,
            )
            resp.raise_for_status()
        logger.info("GHL: updated contact %s", contact_id)
        return resp.json().get("contact", {})

    async def add_tags(self, contact_id: str, tags: list[str]) -> dict:
        """Add tags to a contact."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/contacts/{contact_id}/tags",
                headers=self._headers(),
                json={"tags": tags},
            )
            resp.raise_for_status()
        return resp.json()

    # ── Opportunities (Pipeline) ──────────────────────────────────────

    async def list_pipelines(self) -> list[dict]:
        """List all sales pipelines for the location."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/opportunities/pipelines",
                headers=self._headers(),
                params={"locationId": self.LOCATION_ID},
            )
            resp.raise_for_status()
        return resp.json().get("pipelines", [])

    async def search_opportunities(
        self,
        pipeline_id: str = "",
        stage_id: str = "",
        status: str = "",
        query: str = "",
        limit: int = 20,
    ) -> list[dict]:
        """Search pipeline opportunities."""
        params: dict[str, Any] = {
            "location_id": self.LOCATION_ID,
            "limit": limit,
        }
        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        if stage_id:
            params["pipeline_stage_id"] = stage_id
        if status:
            params["status"] = status
        if query:
            params["q"] = query

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/opportunities/search",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
        return resp.json().get("opportunities", [])

    async def create_opportunity(
        self,
        pipeline_id: str,
        stage_id: str,
        contact_id: str,
        name: str,
        monetary_value: float = 0.0,
        status: str = "open",
    ) -> dict:
        """Create a new pipeline opportunity (deal)."""
        payload = {
            "pipelineId": pipeline_id,
            "locationId": self.LOCATION_ID,
            "name": name,
            "pipelineStageId": stage_id,
            "status": status,
            "contactId": contact_id,
            "monetaryValue": monetary_value,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/opportunities/",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        result = resp.json().get("opportunity", {})
        logger.info("GHL: created opportunity '%s' (%s)", name, result.get("id"))
        return result

    async def update_opportunity_stage(
        self,
        opportunity_id: str,
        stage_id: str,
        status: str = "",
    ) -> dict:
        """Move an opportunity to a new pipeline stage."""
        payload: dict[str, Any] = {"pipelineStageId": stage_id}
        if status:
            payload["status"] = status

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.put(
                f"{_BASE}/opportunities/{opportunity_id}",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        logger.info("GHL: moved opportunity %s to stage %s", opportunity_id, stage_id)
        return resp.json().get("opportunity", {})

    # ── Conversations & SMS ───────────────────────────────────────────

    async def search_conversations(
        self,
        contact_id: str = "",
        query: str = "",
        limit: int = 20,
    ) -> list[dict]:
        """Search conversations in the GHL location."""
        params: dict[str, Any] = {
            "locationId": self.LOCATION_ID,
            "limit": limit,
        }
        if contact_id:
            params["contactId"] = contact_id
        if query:
            params["query"] = query

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/conversations/search",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
        return resp.json().get("conversations", [])

    async def get_conversation_messages(self, conversation_id: str, limit: int = 20) -> list[dict]:
        """Fetch message history for a conversation."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/conversations/{conversation_id}/messages",
                headers=self._headers(),
                params={"limit": limit},
            )
            resp.raise_for_status()
        return resp.json().get("messages", {}).get("messages", [])

    async def send_sms(self, contact_id: str, text: str) -> dict:
        """Send an outbound SMS to a contact via GHL conversations."""
        payload = {
            "type": "SMS",
            "contactId": contact_id,
            "message": text,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/conversations/messages",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        result = resp.json()
        logger.info("GHL: sent SMS to contact %s", contact_id)
        return result

    async def send_email(
        self,
        contact_id: str,
        subject: str,
        body_html: str,
        from_name: str = "",
    ) -> dict:
        """Send an outbound email to a contact via GHL."""
        payload: dict[str, Any] = {
            "type": "Email",
            "contactId": contact_id,
            "subject": subject,
            "emailBody": body_html,
        }
        if from_name:
            payload["fromName"] = from_name

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/conversations/messages",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        logger.info("GHL: sent email to contact %s — '%s'", contact_id, subject)
        return resp.json()

    # ── AI query stub ─────────────────────────────────────────────────

    async def query(
        self,
        text: str,
        intent: str = "CRM",
        topic: str = "",
        context: str = "eagle_eye",
        user: str = "user",
    ) -> str:
        """Translate a natural-language CRM query into a GHL API call.

        Simple keyword dispatch — for advanced NL→GHL routing use the
        intent classifier to pick this backend, then process the structured
        intent in the webhook handler or a dedicated skill.
        """
        t = text.lower()

        if any(k in t for k in ["search contact", "find contact", "look up contact"]):
            query_term = text.split("contact")[-1].strip()
            contacts = await self.search_contacts(query=query_term, limit=5)
            if not contacts:
                return f"No contacts found matching '{query_term}' in GoHighLevel."
            lines = [
                f"- {c.get('contactName') or c.get('firstName', '')} {c.get('lastName', '')} "
                f"({c.get('email', '')} / {c.get('phone', '')})"
                for c in contacts
            ]
            return f"Found {len(contacts)} contact(s):\n" + "\n".join(lines)

        if any(k in t for k in ["pipeline", "opportunities", "deals"]):
            opps = await self.search_opportunities(limit=10)
            if not opps:
                return "No open opportunities found in GoHighLevel pipeline."
            lines = [
                f"- {o.get('name')} | Stage: {o.get('pipelineStage', {}).get('name', '?')} "
                f"| ${o.get('monetaryValue', 0):,.0f}"
                for o in opps
            ]
            return f"Open opportunities ({len(opps)}):\n" + "\n".join(lines)

        return (
            "GoHighLevel CRM is connected. I can:\n"
            "• Search contacts — 'find contact John Smith'\n"
            "• Show pipeline — 'show my pipeline'\n"
            "• Send SMS — handled via webhook automations\n"
            "What would you like to do?"
        )
