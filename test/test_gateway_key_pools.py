"""Unit tests for named key pools in srv.gateway (no network: a fake adapter stands in for fal).

Run: pytest test/test_gateway_key_pools.py
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cli.core import HttpProviderError, Response
from srv import gateway


class FakeAdapter:
    """Records the key each call ran on; mimics the adapter interface the gateway uses."""

    calls: list[tuple[str, str]] = []
    locked_keys: set[str] = set()

    def __init__(self, api_key: str, config=None):
        self.api_key = api_key
        self.api_keys = [api_key]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def _response(self, status: str = "queued") -> Response:
        return Response(request_id=f"req-{self.api_key}", status=status)

    def _record(self, op: str) -> None:
        if self.api_key in self.locked_keys:
            raise HttpProviderError(401, "unauthorized", raw_response=None)
        FakeAdapter.calls.append((op, self.api_key))

    def submit_async(self, model, webhook, **_):
        self._record("submit_async")
        return self._response()

    def submit(self, model, **_):
        self._record("submit")
        return self._response("completed")

    def status(self, *_):
        self._record("status")
        return self._response("processing")

    def cancel(self, *_):
        self._record("cancel")
        return self._response("cancelled")

    def upload(self, data, content_type, file_name, headers=None):
        self._record("upload")
        return f"https://cdn.example/{self.api_key}"


@pytest.fixture
def client(monkeypatch):
    for var in ("FAL_KEYS", "FAL_KEY", "FAL_API_KEY", "FAL_KEYS_PARADISE", "FAL_KEYS_EMPTY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("FAL_KEYS", "shared-1,shared-2")
    monkeypatch.setenv("FAL_KEYS_PARADISE", "paradise-1")
    monkeypatch.setattr(gateway, "PROVIDERS", {"fal": FakeAdapter})
    monkeypatch.setattr(gateway, "_pools", {})
    FakeAdapter.calls = []
    FakeAdapter.locked_keys = set()
    with TestClient(gateway.app) as test_client:
        yield test_client


def _submit_async(client, **extra):
    body = {"provider": "fal", "model": "m", "input": {}, "webhook": "https://hook", **extra}
    return client.post("/v1/submit_async", json=body)


def test_named_pool_bills_only_its_key(client):
    for _ in range(10):
        response = _submit_async(client, key_pool="paradise")
        assert response.status_code == 200
        assert response.json()["key_pool"] == "paradise"
        assert response.json()["key_ref"] == gateway.key_ref("paradise-1")
    assert {key for _, key in FakeAdapter.calls} == {"paradise-1"}


def test_default_pool_never_uses_named_keys(client):
    for _ in range(10):
        response = _submit_async(client)
        assert response.status_code == 200
        assert response.json()["key_pool"] is None
    assert {key for _, key in FakeAdapter.calls} <= {"shared-1", "shared-2"}


def test_unconfigured_named_pool_is_503_not_fallback(client):
    response = _submit_async(client, key_pool="empty")
    assert response.status_code == 503
    assert "fal:empty" in response.json()["error"]
    assert FakeAdapter.calls == []


def test_dead_named_key_does_not_fail_over_to_shared(client):
    FakeAdapter.locked_keys = {"paradise-1"}
    response = _submit_async(client, key_pool="paradise")
    assert response.status_code == 503
    assert FakeAdapter.calls == []


@pytest.mark.parametrize("bad", ["Paradise", "../x", "a-b", "", "x" * 33])
def test_invalid_pool_name_rejected(client, bad):
    response = _submit_async(client, key_pool=bad)
    assert response.status_code == 400
    assert FakeAdapter.calls == []


def test_follow_ups_and_blocking_submit_use_named_pool(client):
    follow_up = {"provider": "fal", "model": "m", "request_id": "r", "key_pool": "paradise"}
    assert client.post("/v1/status", json=follow_up).json()["key_pool"] == "paradise"
    assert client.post("/v1/cancel", json=follow_up).json()["key_pool"] == "paradise"
    blocking = client.post("/v1/submit", json={"provider": "fal", "model": "m", "key_pool": "paradise", "timeout": 5})
    assert blocking.json()["key_pool"] == "paradise"
    assert [key for _, key in FakeAdapter.calls] == ["paradise-1"] * 3


def test_upload_query_param_pool(client):
    response = client.post(
        "/v1/upload?provider=fal&key_pool=paradise", content=b"x", headers={"Content-Type": "image/png"}
    )
    assert response.json() == {
        "provider": "fal",
        "key_pool": "paradise",
        "url": "https://cdn.example/paradise-1",
        "key_ref": gateway.key_ref("paradise-1"),
    }


def test_health_lists_named_pools(client):
    body = client.get("/health").json()
    assert body["providers"] == {"fal": 2}
    assert body["key_pools"] == {"fal:paradise": 1}
