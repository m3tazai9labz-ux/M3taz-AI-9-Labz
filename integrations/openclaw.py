"""OpenClaw integration — Personal AI agent daemon / skills engine client.

OpenClaw runs as a persistent daemon and exposes an HTTP API.
We use it for:
  - Automation tasks (scheduling, triggers)
  - Platform skills not natively handled by our hub
  - Long-running background tasks
"""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)


class OpenClawClient:
    """Client for the OpenClaw local API."""

    BASE_URL = config.OPENCLAW_API_URL
    API_KEY = config.OPENCLAW_API_KEY

    async def query(
        self,
        text: str,
        intent: str = "AUTOMATION",
        topic: str = "",
        context: str = "personal",
        user: str = "user",
    ) -> str:
        payload = {
            "message": text,
            "context": context,
            "user": user,
            "metadata": {"intent": intent, "topic": topic},
        }
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["X-API-Key"] = self.API_KEY

        logger.info("OpenClaw dispatch: intent=%s text=%.60s", intent, text)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/message",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response") or data.get("text") or str(data)

    async def run_skill(self, skill_name: str, params: dict) -> str:
        """Invoke a specific OpenClaw skill by name."""
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["X-API-Key"] = self.API_KEY

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/skills/{skill_name}/run",
                headers=headers,
                json=params,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result") or str(data)
