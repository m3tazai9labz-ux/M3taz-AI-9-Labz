"""Twin.so AI automation client.

Wraps the Twin.so REST API (https://twin.so) using the httpx library
(already a project dependency) to trigger automated web tasks and
retrieve their results.

Usage
-----
    from execution.twin_client import TwinClient

    async with TwinClient() as client:
        task = await client.create_task(
            description="Go to amazon.com and find the top-rated wireless headphones",
        )
        result = await client.get_task(task["id"])
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx

from config import TWIN_API_BASE_URL, TWIN_API_KEY, TWIN_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

_TIMEOUT = 30  # seconds


class TwinClientError(Exception):
    """Raised when the Twin.so API returns an error."""


class TwinClient:
    """Async HTTP client for the Twin.so API.

    Can be used as an async context manager::

        async with TwinClient() as client:
            task = await client.create_task(description="...")

    Or instantiated directly (call ``await client.aclose()`` when done)::

        client = TwinClient(api_key="sk_live_...")
        task = await client.create_task(description="...")
        await client.aclose()
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or TWIN_API_KEY
        self._base_url = (base_url or TWIN_API_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._build_headers(),
            timeout=_TIMEOUT,
        )

    # ── lifecycle ──────────────────────────────────────────────────

    async def __aenter__(self) -> "TwinClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # ── private helpers ────────────────────────────────────────────

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TwinClientError(
                f"Twin.so API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise TwinClientError(f"Twin.so request failed: {exc}") from exc

        return response.json()

    # ── public API methods ─────────────────────────────────────────

    async def create_task(
        self,
        description: str,
        *,
        context: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Create and submit a new automated task on Twin.so.

        Parameters
        ----------
        description:
            Plain-language description of what the agent should do.
        context:
            Optional structured context (URLs, credentials, etc.) passed
            to the agent.
        webhook_url:
            Optional URL that Twin.so will POST results to when the task
            completes.

        Returns
        -------
        dict
            The created task object returned by the Twin.so API.
        """
        payload: dict[str, Any] = {"description": description}
        if context:
            payload["context"] = context
        if webhook_url:
            payload["webhook_url"] = webhook_url

        logger.info("Creating Twin.so task: %.80s", description)
        return await self._request("POST", "/tasks", json=payload)

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Retrieve the status and result of a previously created task.

        Parameters
        ----------
        task_id:
            The ``id`` returned by :meth:`create_task`.

        Returns
        -------
        dict
            Task object including ``status`` and ``result`` fields.
        """
        logger.info("Fetching Twin.so task %s", task_id)
        return await self._request("GET", f"/tasks/{task_id}")

    async def list_tasks(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """List recent tasks created under the current API key.

        Parameters
        ----------
        limit:
            Maximum number of tasks to return (default 20).
        offset:
            Pagination offset.

        Returns
        -------
        list[dict]
            List of task objects.
        """
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", "/tasks", params=params)


# ── Webhook verification ───────────────────────────────────────────


def verify_twin_signature(payload: bytes, signature: str) -> bool:
    """Verify that an incoming webhook originated from Twin.so.

    Twin.so signs webhook payloads with HMAC-SHA256 using the secret
    configured in ``TWIN_WEBHOOK_SECRET``.  This function returns
    ``True`` only when the signature matches.

    Parameters
    ----------
    payload:
        The raw request body bytes.
    signature:
        The value of the ``X-Twin-Signature`` HTTP header sent by Twin.so.

    Returns
    -------
    bool
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    if not TWIN_WEBHOOK_SECRET:
        logger.warning(
            "TWIN_WEBHOOK_SECRET is not set — skipping webhook signature verification."
        )
        return True  # allow through when secret is not configured

    expected = hmac.new(
        TWIN_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
