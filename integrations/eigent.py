"""Eigent AI integration — Multi-agent workforce client.

Supports: developer, browser, document, multimodal agent types.
"""

from __future__ import annotations

import logging

import httpx

import config
from orchestration.intent_classifier import Intent

logger = logging.getLogger(__name__)

# Map intents to the best Eigent agent type
INTENT_TO_AGENT = {
    Intent.CODE: "developer",
    Intent.RESEARCH: "browser",
    Intent.DOCUMENT: "document",
    Intent.TASK: "browser",        # general task: browser agent orchestrates
    Intent.AUTOMATION: "developer",
}


class EigentClient:
    """Client for the Eigent AI multi-agent API."""

    BASE_URL = config.EIGENT_API_URL
    API_KEY = config.EIGENT_API_KEY

    def _agent_type(self, intent: str) -> str:
        return INTENT_TO_AGENT.get(intent, "browser")

    async def query(
        self,
        text: str,
        intent: str = "TASK",
        topic: str = "",
        context: str = "eagle_eye",
        user: str = "user",
    ) -> str:
        agent_type = self._agent_type(intent)
        payload = {
            "task": text,
            "agent_type": agent_type,
            "context": {
                "business_context": context,
                "topic": topic,
                "user": user,
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"

        logger.info("Eigent dispatch: agent_type=%s task=%.60s", agent_type, text)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/v1/tasks",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # Eigent returns result in 'result' or 'output' key
            return data.get("result") or data.get("output") or str(data)
