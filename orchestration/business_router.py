"""M3ta'z Kub3 — Business Context Router.

Maps (intent, chat_context) to the right AI backend and calls it.
Falls back through the preference list until one succeeds.
"""

from __future__ import annotations

import logging

import config
from orchestration.intent_classifier import Intent

logger = logging.getLogger(__name__)

# Intent → preferred backends (in priority order)
INTENT_BACKEND_MAP: dict[str, list[str]] = {
    Intent.CHAT: ["open_webui", "ollama", "anthropic"],
    Intent.TASK: ["eigent", "agent_zero", "open_webui"],
    Intent.RESEARCH: ["eigent", "anythingllm", "agent_zero"],
    Intent.CODE: ["eigent", "agent_zero"],
    Intent.DEEP_REASONING: ["agent_zero", "open_webui"],
    Intent.KNOWLEDGE: ["anythingllm", "affine", "open_webui"],
    Intent.DOCUMENT: ["eigent", "anythingllm", "affine"],
    Intent.CRM: ["gohighlevel", "eigent"],
    Intent.AUTOMATION: ["openclaw", "eigent"],
    Intent.CONTENT_INGEST: [],
}


def _preferred_backends(intent: str, chat_context: str) -> list[str]:
    """Return ordered list of backends to try for this intent + context."""
    context_prefs = config.CONTEXT_AI_PREFERENCE.get(chat_context, [])
    intent_prefs = INTENT_BACKEND_MAP.get(intent, ["open_webui"])
    # Merge: context preference first, then fill with intent preference
    seen: set[str] = set()
    merged = []
    for b in context_prefs + intent_prefs:
        if b not in seen:
            seen.add(b)
            merged.append(b)
    return merged or ["open_webui"]


class BusinessRouter:
    """Dispatches to the right AI backend based on intent and business context."""

    async def dispatch(self, intent: str, topic: str, message) -> tuple[str, str]:
        """Try each preferred backend in order. Return (response_text, backend_name)."""
        from integrations.open_webui import OpenWebUIClient
        from integrations.eigent import EigentClient
        from integrations.agent_zero import AgentZeroClient
        from integrations.affine import AFFiNEClient
        from integrations.openclaw import OpenClawClient
        from integrations.ollama import OllamaClient
        from integrations.anythingllm import AnythingLLMClient
        from integrations.gohighlevel import GHLClient

        clients = {
            "open_webui": OpenWebUIClient(),
            "eigent": EigentClient(),
            "agent_zero": AgentZeroClient(),
            "affine": AFFiNEClient(),
            "openclaw": OpenClawClient(),
            "ollama": OllamaClient(),
            "anythingllm": AnythingLLMClient(),
            "gohighlevel": GHLClient(),
            "anthropic": None,  # direct fallback handled below
        }

        backends = _preferred_backends(intent, message.chat_context)

        for backend_name in backends:
            client = clients.get(backend_name)
            if client is None and backend_name == "anthropic":
                try:
                    result = await self._call_anthropic_direct(message.text, message.chat_context)
                    return result, "anthropic"
                except Exception as exc:
                    logger.warning("anthropic direct failed: %s", exc)
                    continue

            if client is None:
                continue

            try:
                logger.info("Trying backend: %s", backend_name)
                result = await client.query(
                    text=message.text,
                    intent=intent,
                    topic=topic,
                    context=message.chat_context,
                    user=message.username,
                )
                return result, backend_name
            except Exception as exc:
                logger.warning("Backend %s failed: %s", backend_name, exc)
                continue

        # Hard fallback: direct Anthropic call
        try:
            result = await self._call_anthropic_direct(message.text, message.chat_context)
            return result, "anthropic_fallback"
        except Exception as exc:
            raise RuntimeError("All backends exhausted") from exc

    async def _call_anthropic_direct(self, text: str, chat_context: str) -> str:
        """Direct Claude API call as the final fallback."""
        import httpx

        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("No ANTHROPIC_API_KEY configured")

        system = (
            f"You are M3ta'z AI assistant for the '{chat_context}' business context. "
            "Be helpful, concise, and professional."
        )
        payload = {
            "model": config.ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": text}],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": config.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
