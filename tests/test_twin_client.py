"""Tests for execution.twin_client."""

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from execution.twin_client import TwinClient, TwinClientError, verify_twin_signature


# ── TwinClient unit tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task_sends_correct_payload():
    """create_task should POST description and optional fields to /tasks."""
    fake_response = {"id": "task_123", "status": "queued"}

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = fake_response
    mock_response.raise_for_status = MagicMock()
    mock_client.request.return_value = mock_response

    client = TwinClient(api_key="test_key")
    client._client = mock_client

    result = await client.create_task(
        description="Search for best Python books",
        webhook_url="https://example.com/webhook/twin",
    )

    mock_client.request.assert_called_once_with(
        "POST",
        "/tasks",
        json={
            "description": "Search for best Python books",
            "webhook_url": "https://example.com/webhook/twin",
        },
    )
    assert result == fake_response


@pytest.mark.asyncio
async def test_get_task_calls_correct_path():
    """get_task should GET /tasks/{task_id}."""
    fake_response = {"id": "task_abc", "status": "completed", "result": "done"}

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = fake_response
    mock_response.raise_for_status = MagicMock()
    mock_client.request.return_value = mock_response

    client = TwinClient(api_key="test_key")
    client._client = mock_client

    result = await client.get_task("task_abc")

    mock_client.request.assert_called_once_with("GET", "/tasks/task_abc")
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_list_tasks_passes_pagination_params():
    """list_tasks should forward limit/offset as query params."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client.request.return_value = mock_response

    client = TwinClient(api_key="test_key")
    client._client = mock_client

    await client.list_tasks(limit=5, offset=10)

    mock_client.request.assert_called_once_with(
        "GET", "/tasks", params={"limit": 5, "offset": 10}
    )


@pytest.mark.asyncio
async def test_http_status_error_raises_twin_client_error():
    """Non-2xx responses should be wrapped in TwinClientError."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(),
        response=mock_response,
    )
    mock_client.request.return_value = mock_response

    client = TwinClient(api_key="bad_key")
    client._client = mock_client

    with pytest.raises(TwinClientError, match="401"):
        await client.create_task(description="will fail")


@pytest.mark.asyncio
async def test_request_error_raises_twin_client_error():
    """Network errors should be wrapped in TwinClientError."""
    mock_client = AsyncMock()
    mock_client.request.side_effect = httpx.ConnectError("Connection refused")

    client = TwinClient(api_key="test_key")
    client._client = mock_client

    with pytest.raises(TwinClientError, match="request failed"):
        await client.get_task("task_xyz")


@pytest.mark.asyncio
async def test_context_manager_closes_client():
    """Using TwinClient as async context manager should call aclose."""
    with patch.object(TwinClient, "aclose", new_callable=AsyncMock) as mock_close:
        async with TwinClient(api_key="key") as client:
            assert client is not None
        mock_close.assert_awaited_once()


# ── verify_twin_signature tests ────────────────────────────────────


def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    payload = b'{"id": "t1", "status": "completed"}'
    secret = "my_webhook_secret"
    sig = _sign(payload, secret)

    with patch("execution.twin_client.TWIN_WEBHOOK_SECRET", secret):
        assert verify_twin_signature(payload, sig) is True


def test_invalid_signature_returns_false():
    payload = b'{"id": "t1", "status": "completed"}'
    secret = "my_webhook_secret"

    with patch("execution.twin_client.TWIN_WEBHOOK_SECRET", secret):
        assert verify_twin_signature(payload, "badsignature") is False


def test_no_secret_configured_allows_through():
    """When TWIN_WEBHOOK_SECRET is empty the function should return True."""
    with patch("execution.twin_client.TWIN_WEBHOOK_SECRET", ""):
        assert verify_twin_signature(b"payload", "any_signature") is True


@pytest.mark.asyncio
async def test_create_task_context_included_when_provided():
    """create_task should include context field in payload when given."""
    fake_response = {"id": "task_999"}

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = fake_response
    mock_response.raise_for_status = MagicMock()
    mock_client.request.return_value = mock_response

    client = TwinClient(api_key="test_key")
    client._client = mock_client

    await client.create_task(
        description="Do something",
        context={"url": "https://example.com"},
    )

    call_kwargs = mock_client.request.call_args
    payload = call_kwargs.kwargs["json"]
    assert payload["context"] == {"url": "https://example.com"}
