"""Open WebUI integration — OpenAI-compatible chat API proxy."""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)


class OpenWebUIClient:
    """Sends chat messages to Open WebUI's OpenAI-compatible endpoint."""

    BASE_URL = config.OPEN_WEBUI_URL
    API_KEY = config.OPEN_WEBUI_API_KEY

    async def query(
        self,
        text: str,
        intent: str = "CHAT",
        topic: str = "",
        context: str = "personal",
        user: str = "user",
    ) -> str:
        system = (
            f"You are M3ta'z AI assistant for the '{context}' business context. "
            "Be helpful, concise, and professional."
        )
        payload = {
            "model": "gpt-4o-mini",  # or whichever model is configured in Open WebUI
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
