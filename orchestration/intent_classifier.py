"""M3ta'z Kub3 — Intent Classifier.

Uses Claude (Anthropic) to classify incoming messages into one of the
supported Intent types, and extracts a short topic string.
"""

from __future__ import annotations

import json
import logging
from enum import StrEnum

import httpx

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the intent classifier for M3ta'z A.I. 9 Labz, an enterprise AI hub.

Classify the user message into EXACTLY one intent and extract a short topic.

Intents:
- CHAT          — casual conversation, simple questions, greetings
- TASK          — multi-step autonomous task ("research X and write a report", "book a call")
- RESEARCH      — web search / data gathering ("find me", "search for", "what is the latest")
- CODE          — code writing, debugging, terminal commands
- DEEP_REASONING — complex analysis, long-form reasoning, strategic planning
- KNOWLEDGE     — SOP / wiki / documentation lookup ("what's our process for", "how do we")
- CONTENT_INGEST — explicit save/ingest request or attachment-only message
- AUTOMATION    — schedule or trigger-based automation ("every day at 9am", "when X happens")
- DOCUMENT      — create/edit a doc, slide deck, report, or structured output
- CRM           — contact/lead/deal management ("find contact", "add lead", "update pipeline", "show deals", "send SMS to client")

Reply with ONLY valid JSON (no markdown):
{
  "intent": "<INTENT>",
  "topic": "<3-6 word topic summary>"
}
"""


class Intent(StrEnum):
    CHAT = "CHAT"
    TASK = "TASK"
    RESEARCH = "RESEARCH"
    CODE = "CODE"
    DEEP_REASONING = "DEEP_REASONING"
    KNOWLEDGE = "KNOWLEDGE"
    CONTENT_INGEST = "CONTENT_INGEST"
    AUTOMATION = "AUTOMATION"
    DOCUMENT = "DOCUMENT"
    CRM = "CRM"


class IntentClassifier:
    """Classifies message intent using Claude."""

    def __init__(self) -> None:
        self._api_key = config.ANTHROPIC_API_KEY
        self._model = config.ANTHROPIC_MODEL

    async def classify(self, text: str, chat_context: str) -> tuple[str, str]:
        """Return (intent, topic). Falls back to CHAT on any error."""
        if not text or not text.strip():
            return Intent.CONTENT_INGEST, "media attachment"

        if not self._api_key:
            return self._heuristic(text)

        try:
            result = await self._call_claude(text, chat_context)
            return result
        except Exception as exc:
            logger.warning("Claude classification failed, using heuristic: %s", exc)
            return self._heuristic(text)

    async def _call_claude(self, text: str, chat_context: str) -> tuple[str, str]:
        user_content = f"[Business context: {chat_context}]\n\nMessage: {text}"
        payload = {
            "model": self._model,
            "max_tokens": 100,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}],
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["content"][0]["text"].strip()
            data = json.loads(content)
            intent = data.get("intent", "CHAT").upper()
            topic = data.get("topic", "")
            # Validate intent
            if intent not in Intent.__members__:
                intent = "CHAT"
            return intent, topic

    def _heuristic(self, text: str) -> tuple[str, str]:
        """Simple keyword-based fallback when API is unavailable."""
        t = text.lower()
        if any(k in t for k in ["write code", "debug", "function", "script", "terminal", "bash"]):
            return Intent.CODE, "code task"
        if any(k in t for k in ["search", "find", "research", "look up", "what is"]):
            return Intent.RESEARCH, "research query"
        if any(k in t for k in ["create doc", "write report", "make a slide", "draft"]):
            return Intent.DOCUMENT, "document creation"
        if any(k in t for k in ["every day", "every hour", "schedule", "automate", "when "]):
            return Intent.AUTOMATION, "automation task"
        if any(k in t for k in ["our process", "sop", "how do we", "policy", "procedure"]):
            return Intent.KNOWLEDGE, "knowledge lookup"
        if any(k in t for k in ["analyze", "strategy", "plan", "think through", "reasoning"]):
            return Intent.DEEP_REASONING, "deep analysis"
        if any(k in t for k in [
            "contact", "lead", "deal", "pipeline", "opportunity", "crm",
            "send sms", "send email to client", "add contact", "find contact",
            "update lead", "gohighlevel", "ghl", "lark crm",
        ]):
            return Intent.CRM, "CRM operation"
        if any(k in t for k in ["do this", "complete", "task", "handle", "manage", "run"]):
            return Intent.TASK, "general task"
        return Intent.CHAT, "conversation"
