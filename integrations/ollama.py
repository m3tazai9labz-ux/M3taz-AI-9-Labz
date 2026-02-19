"""Ollama integration — Local model inference client.

Ollama runs local LLMs (Llama, Mistral, Gemma, Qwen, etc.) and exposes
an Anthropic-compatible API at http://localhost:11434.

This client can be used:
  1. Directly via the Ollama REST API
  2. As an Anthropic-compatible API (for Claude Code + local models)

Recommended models for M3ta'z Hub:
  - qwen3-coder     (code generation)
  - glm-4.7         (general tasks)
  - gpt-oss:20b     (cost-effective general)
  - gpt-oss:120b    (high-capability general)

See: https://ollama.com/search for available models
"""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama's REST API (OpenAI-compatible /api/chat endpoint)."""

    BASE_URL = config.OLLAMA_URL
    DEFAULT_MODEL = config.OLLAMA_MODEL

    async def query(
        self,
        text: str,
        intent: str = "CHAT",
        topic: str = "",
        context: str = "personal",
        user: str = "user",
        model: str | None = None,
    ) -> str:
        chosen_model = model or self.DEFAULT_MODEL
        system = (
            f"You are M3ta'z AI assistant for the '{context}' business context. "
            "Be helpful, concise, and professional."
        )
        payload = {
            "model": chosen_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "stream": False,
        }

        logger.info("Ollama query: model=%s intent=%s text=%.60s", chosen_model, intent, text)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    async def list_models(self) -> list[str]:
        """Return list of locally available model names."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.BASE_URL}/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]

    async def pull_model(self, model_name: str) -> None:
        """Pull a model from Ollama registry (non-blocking fire-and-forget log)."""
        logger.info("Pulling Ollama model: %s", model_name)
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/api/pull",
                json={"name": model_name},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        logger.debug("pull: %s", line)
        logger.info("Model pulled: %s", model_name)
