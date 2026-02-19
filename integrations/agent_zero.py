"""Agent Zero integration — Hierarchical agent / deep reasoning client."""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)


class AgentZeroClient:
    """Client for the Agent Zero REST API."""

    BASE_URL = config.AGENT_ZERO_URL
    API_KEY = config.AGENT_ZERO_API_KEY

    async def query(
        self,
        text: str,
        intent: str = "DEEP_REASONING",
        topic: str = "",
        context: str = "meta",
        user: str = "user",
    ) -> str:
        payload = {
            "message": text,
            "context": {
                "business_context": context,
                "topic": topic,
                "user": user,
                "intent": intent,
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"

        logger.info("Agent Zero dispatch: intent=%s text=%.60s", intent, text)
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/chat",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response") or data.get("message") or str(data)
