"""Lark (LarkSuite) integration — messaging, CRM (Bitable), and document client.

Lark is ByteDance's enterprise collaboration platform. We use it for:
  - Inbound/outbound messaging (Lark bot in eagle_eye and lotus_group chats)
  - Lark Base (Bitable) as a lightweight CRM / lead tracker
  - Lark Docs for reading/ingesting internal knowledge documents

International API base: https://open.larksuite.com/open-apis/
    (Use https://open.feishu.cn/open-apis/ for Mainland China tenants)

Authentication flow:
  1. POST /auth/v3/tenant_access_token/internal  → token (valid 2 hours)
  2. Pass token as:  Authorization: Bearer <token>

Docs: https://open.larksuite.com/document
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

_BASE = config.LARK_API_BASE  # e.g. https://open.larksuite.com/open-apis


class _TokenCache:
    """Simple in-process cache for the tenant access token (TTL 2 hours)."""

    def __init__(self) -> None:
        self._token: str = ""
        self._expires_at: float = 0.0

    def is_valid(self) -> bool:
        return bool(self._token) and time.time() < self._expires_at - 60

    def set(self, token: str, expire: int) -> None:
        self._token = token
        self._expires_at = time.time() + expire

    @property
    def token(self) -> str:
        return self._token


_token_cache = _TokenCache()


class LarkClient:
    """Client for the Lark Open Platform API."""

    APP_ID = config.LARK_APP_ID
    APP_SECRET = config.LARK_APP_SECRET
    VERIFY_TOKEN = config.LARK_VERIFY_TOKEN
    ENCRYPT_KEY = config.LARK_ENCRYPT_KEY

    # ── Auth ──────────────────────────────────────────────────────────

    async def _get_token(self) -> str:
        """Return a valid tenant access token, refreshing if needed."""
        if _token_cache.is_valid():
            return _token_cache.token

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.APP_ID, "app_secret": self.APP_SECRET},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Lark auth failed: {data.get('msg')}")

        _token_cache.set(data["tenant_access_token"], data.get("expire", 7200))
        logger.debug("Lark: refreshed tenant access token")
        return _token_cache.token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ── Messaging ─────────────────────────────────────────────────────

    async def send_message(
        self,
        receive_id: str,
        text: str,
        receive_id_type: str = "open_id",
    ) -> dict:
        """Send a text message to a user or chat.

        receive_id_type: 'open_id' | 'user_id' | 'chat_id' | 'email'
        """
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": f'{{"text": "{text}"}}',
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/im/v1/messages?receive_id_type={receive_id_type}",
                headers=await self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark send_message failed: %s", data.get("msg"))
        else:
            logger.info("Lark: sent message to %s", receive_id)
        return data

    async def reply_message(self, message_id: str, text: str) -> dict:
        """Reply to a specific message thread."""
        payload = {
            "msg_type": "text",
            "content": f'{{"text": "{text}"}}',
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/im/v1/messages/{message_id}/reply",
                headers=await self._headers(),
                json=payload,
            )
            resp.raise_for_status()
        return resp.json()

    async def query(
        self,
        text: str,
        intent: str = "CHAT",
        topic: str = "",
        context: str = "eagle_eye",
        user: str = "user",
    ) -> str:
        """Route an inbound Lark message to the AI hub and return the response.

        This is called by business_router; the actual AI dispatch happens
        upstream — this method is the stub that lets Lark appear as an
        AI backend in the routing table for CONTEXT-level preference.
        """
        # The business router calls this, but Lark isn't an AI backend —
        # it's a platform we READ from and WRITE to. Return an informational
        # response so the router can fall through to the next backend.
        raise NotImplementedError(
            "LarkClient.query() is not an AI backend. "
            "Use send_message() / reply_message() to respond to Lark events."
        )

    # ── CRM / Lark Base (Bitable) ─────────────────────────────────────

    async def list_crm_records(
        self,
        app_token: str,
        table_id: str,
        filter_expr: str = "",
        page_size: int = 20,
    ) -> list[dict]:
        """List records from a Lark Base table (used as lightweight CRM).

        app_token: found in the Bitable URL  → https://xxx.larksuite.com/base/<app_token>
        table_id:  found in the Bitable table URL fragment
        filter_expr: Bitable filter string e.g. 'AND(CurrentValue.[Stage]="Prospect")'
        """
        params: dict[str, Any] = {"page_size": page_size}
        if filter_expr:
            params["filter"] = filter_expr

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers=await self._headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark Base list_records failed: %s", data.get("msg"))
            return []

        return data.get("data", {}).get("items", [])

    async def create_crm_record(
        self,
        app_token: str,
        table_id: str,
        fields: dict,
    ) -> dict:
        """Create a new record in a Lark Base table."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers=await self._headers(),
                json={"fields": fields},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark Base create_record failed: %s", data.get("msg"))
        return data.get("data", {}).get("record", {})

    async def update_crm_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: dict,
    ) -> dict:
        """Update fields on an existing Lark Base record."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.put(
                f"{_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                headers=await self._headers(),
                json={"fields": fields},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark Base update_record failed: %s", data.get("msg"))
        return data.get("data", {}).get("record", {})

    # ── Documents ─────────────────────────────────────────────────────

    async def get_doc_content(self, document_id: str) -> str:
        """Fetch the raw text content of a Lark Doc for RAG ingestion."""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{_BASE}/docx/v1/documents/{document_id}/raw_content",
                headers=await self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark get_doc_content failed: %s", data.get("msg"))
            return ""
        return data.get("data", {}).get("content", "")

    async def list_wiki_nodes(self, space_id: str, parent_node_token: str = "") -> list[dict]:
        """List pages in a Lark Wiki space."""
        params: dict[str, Any] = {"space_id": space_id, "page_size": 50}
        if parent_node_token:
            params["parent_node_token"] = parent_node_token

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/wiki/v2/spaces/{space_id}/nodes",
                headers=await self._headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error("Lark list_wiki_nodes failed: %s", data.get("msg"))
            return []
        return data.get("data", {}).get("items", [])

    # ── Webhook Verification ──────────────────────────────────────────

    @staticmethod
    def verify_webhook_signature(
        timestamp: str,
        nonce: str,
        body: bytes,
        signature: str,
    ) -> bool:
        """Verify a Lark webhook event signature.

        Lark signs events as:
          HMAC-SHA256( encrypt_key + timestamp + nonce + body_string )
        """
        if not config.LARK_ENCRYPT_KEY:
            return True  # skip verification if not configured

        token = config.LARK_ENCRYPT_KEY + timestamp + nonce + body.decode()
        expected = hmac.new(
            config.LARK_ENCRYPT_KEY.encode(),
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def build_challenge_response(challenge: str) -> dict:
        """Return the challenge-response payload for Lark URL verification."""
        return {"challenge": challenge}
