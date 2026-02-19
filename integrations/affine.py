"""AFFiNE integration — Knowledge base / workspace client.

AFFiNE exposes a GraphQL API and a JSON-RPC interface.
We use the GraphQL API to search documents and create pages.
"""

from __future__ import annotations

import logging

import httpx

import config

logger = logging.getLogger(__name__)

SEARCH_QUERY = """
query SearchDocs($query: String!) {
  searchPages(query: $query, first: 5) {
    edges {
      node {
        id
        title
        content
        updatedAt
      }
    }
  }
}
"""


class AFFiNEClient:
    """Client for AFFiNE GraphQL API."""

    BASE_URL = config.AFFINE_URL
    API_KEY = config.AFFINE_API_KEY

    async def query(
        self,
        text: str,
        intent: str = "KNOWLEDGE",
        topic: str = "",
        context: str = "personal",
        user: str = "user",
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"

        payload = {
            "query": SEARCH_QUERY,
            "variables": {"query": text},
        }
        logger.info("AFFiNE search: query=%.60s", text)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/graphql",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        edges = data.get("data", {}).get("searchPages", {}).get("edges", [])
        if not edges:
            return f"No documents found in the knowledge base for: {text}"

        results = []
        for edge in edges[:3]:
            node = edge["node"]
            title = node.get("title", "Untitled")
            content = node.get("content", "")[:300]
            results.append(f"**{title}**\n{content}")

        return "\n\n---\n\n".join(results)

    async def create_page(self, title: str, content: str, workspace: str = "default") -> dict:
        """Create a new page in AFFiNE. Returns the created page info."""
        headers = {"Content-Type": "application/json"}
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"

        mutation = """
        mutation CreatePage($workspaceId: String!, $title: String!, $content: String!) {
          createPage(workspaceId: $workspaceId, title: $title, content: $content) {
            id
            title
          }
        }
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/graphql",
                headers=headers,
                json={
                    "query": mutation,
                    "variables": {
                        "workspaceId": workspace,
                        "title": title,
                        "content": content,
                    },
                },
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("createPage", {})
