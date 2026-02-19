"""AnythingLLM integration — RAG-powered document chat client.

AnythingLLM provides workspace-based document management with RAG (retrieval-
augmented generation). Each business context maps to its own workspace,
so Eagle Eye, Lotus Group, Meta, etc. each have their own document library.

Key features used:
  - Chat with workspace (RAG over uploaded documents)
  - Document upload (ingest PDFs, docs, links)
  - Workspace management

API Docs: http://localhost:3001/api/docs
Docker:   docker run -d -p 3001:3001 mintplexlabs/anythingllm:master
"""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)

# Business context → AnythingLLM workspace slug
# Slugs are set when you create workspaces in the AnythingLLM UI
CONTEXT_WORKSPACE_MAP: dict[str, str] = {
    "eagle_eye": "eagle-eye-vision-labz",
    "lotus_group": "lotus-group",
    "meta": "metaos-q3bi",
    "personal": "personal",
    "family": "family",
}


class AnythingLLMClient:
    """Client for the AnythingLLM REST API."""

    BASE_URL = config.ANYTHINGLLM_URL
    API_KEY = config.ANYTHINGLLM_API_KEY

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.API_KEY:
            h["Authorization"] = f"Bearer {self.API_KEY}"
        return h

    def _workspace_slug(self, context: str) -> str:
        return CONTEXT_WORKSPACE_MAP.get(context, config.ANYTHINGLLM_DEFAULT_WORKSPACE)

    async def query(
        self,
        text: str,
        intent: str = "KNOWLEDGE",
        topic: str = "",
        context: str = "personal",
        user: str = "user",
    ) -> str:
        """Chat with the workspace that matches the business context."""
        slug = self._workspace_slug(context)
        url = f"{self.BASE_URL}/api/v1/workspace/{slug}/chat"
        payload = {
            "message": text,
            "mode": "chat",   # "chat" uses full conversation history, "query" is single-turn RAG
        }

        logger.info(
            "AnythingLLM query: workspace=%s intent=%s text=%.60s",
            slug, intent, text,
        )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        response_text = data.get("textResponse", "")
        sources = data.get("sources", [])

        # Append source titles if present
        if sources:
            source_titles = [s.get("title", s.get("url", "")) for s in sources[:3]]
            cited = ", ".join(t for t in source_titles if t)
            if cited:
                response_text += f"\n\n_Sources: {cited}_"

        return response_text or "No response from AnythingLLM workspace."

    async def list_workspaces(self) -> list[dict]:
        """Return list of available workspaces."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.BASE_URL}/api/v1/workspaces",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json().get("workspaces", [])

    async def upload_text(self, content: str, filename: str, context: str = "personal") -> bool:
        """Upload a raw text document to a workspace for RAG indexing."""
        slug = self._workspace_slug(context)
        # AnythingLLM accepts raw text via the custom-documents endpoint
        payload = {
            "textContent": content,
            "metadata": {"title": filename},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/v1/workspace/{slug}/upload/raw-text",
                headers=self._headers(),
                json=payload,
            )
            if resp.is_success:
                logger.info("AnythingLLM: uploaded '%s' to workspace '%s'", filename, slug)
                return True
            logger.error(
                "AnythingLLM upload failed: %s %s", resp.status_code, resp.text[:200]
            )
            return False
