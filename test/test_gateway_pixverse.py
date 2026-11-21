"""Unit tests for the PixVerse provider in srv.gateway (no network: a fake adapter stands in).

Run: pytest test/test_gateway_pixverse.py
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cli.core import HttpProviderError, Response
from srv import gateway


class FakePixverse:
    """Records the key and kwargs of each async submit."""

    calls: list[dict] = []
    broke_keys: set[str] = set()

    def __init__(self, api_key: str, config=None):
        del config
        self.api_key = api_key
        self.api_keys = [api_key]

    def submit_async(self, model, webhook, **kwargs):
        if self.api_key in self.broke_keys:
            raise HttpProviderError(402, "PixVerse ErrCode 500090: Insufficient balance")
        FakePixverse.calls.append({"key": self.api_key, "model": model, "webhook": webhook, **kwargs})
        return Response(request_id="42", status="queued")


@pytest.fixture
def client(monkeypatch):
    for var in ("PIXVERSE_KEYS", "PIXVERSE_KEY", "PIXVERSE_API_KEY", "PIXVERSE_WEBHOOK_ID",
                "PIXVERSE_KEYS_FREE_VIDEO", "PIXVERSE_WEBHOOK_ID_FREE_VIDEO", "FAL_KEYS"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("PIXVERSE_KEYS", "paid-1,paid-2")
    monkeypatch.setenv("PIXVERSE_WEBHOOK_ID", "wh-paid")
    monkeypatch.setenv("PIXVERSE_KEYS_FREE_VIDEO", "free-1")
    monkeypatch.setattr(gateway, "PROVIDERS", {"pixverse": FakePixverse})
    monkeypatch.setattr(gateway, "_pools", {})
    FakePixverse.calls = []
    FakePixverse.broke_keys = set()
    with TestClient(gateway.app) as test_client:
        yield test_client


def _submit(client, **extra):
    body = {"provider": "pixverse", "model": "c1/image-to-video", "input": {"prompt": "x", "img_id": 5},
            "webhook": "https://hook/pixverse-webhook", **extra}
    return client.post("/v1/submit_async", json=body)


def test_default_pool_sends_its_webhook_id_and_no_headers(client):
    response = _submit(client, headers={"X-Fal-Store-IO": "0"})
    assert response.status_code == 200, response.text
    (call,) = FakePixverse.calls
    assert call["webhook_id"] == "wh-paid"
    assert "headers" not in call
    assert call["key"] in {"paid-1", "paid-2"}
    assert response.json()["key_pool"] is None


def test_named_pool_needs_its_own_webhook_id(client, monkeypatch):
    response = _submit(client, key_pool="free_video")
    assert response.status_code == 503
    assert "PIXVERSE_WEBHOOK_ID_FREE_VIDEO" in response.json()["error"]
    assert FakePixverse.calls == []

    monkeypatch.setenv("PIXVERSE_WEBHOOK_ID_FREE_VIDEO", "wh-free")
    response = _submit(client, key_pool="free_video")
    assert response.status_code == 200, response.text
    (call,) = FakePixverse.calls
    assert (call["key"], call["webhook_id"]) == ("free-1", "wh-free")
    assert response.json()["key_pool"] == "free_video"


def test_caller_webhook_id_is_kept(client):
    _submit(client, input={"prompt": "x", "img_id": 5, "webhook_id": "explicit"})
    assert FakePixverse.calls[0]["webhook_id"] == "explicit"


def test_out_of_balance_key_fails_over(client):
    FakePixverse.broke_keys = {"paid-1"}
    for _ in range(4):
        assert _submit(client).status_code == 200
    assert {call["key"] for call in FakePixverse.calls} == {"paid-2"}


def test_health_lists_pixverse(client):
    body = client.get("/health").json()
    assert body["providers"] == {"pixverse": 2}
    assert body["key_pools"] == {"pixverse:free_video": 1}
