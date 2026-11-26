"""Unit tests for cli/vidilab.py without network access."""

from __future__ import annotations

import json

import pytest

from cli.core import CapabilityError, ClientConfig, HttpProviderError
from cli.vidilab import Vidilab

# Test fixtures intentionally mirror the existing adapter tests.
# pylint: disable=duplicate-code,redefined-outer-name


class FakeHttpResponse:
    def __init__(self, data, status=200):
        self.status = status
        self.data = json.dumps(data).encode() if not isinstance(data, bytes) else data
        self.headers = {}


class FakePool:
    def __init__(self):
        self.calls: list[dict] = []
        self.status_responses: list[dict] = []

    def request(self, method, url, body=None, headers=None, preload_content=True):
        del preload_content
        self.calls.append({"method": method, "url": url, "body": body, "headers": headers or {}})
        if url.endswith("/uploads"):
            return FakeHttpResponse({"data": {"url": "https://upload.example/image.jpg"}})
        if method == "POST":
            return FakeHttpResponse({"data": {"id": "gen-123", "status": "queued"}}, status=202)
        if self.status_responses:
            return FakeHttpResponse(self.status_responses.pop(0))
        return FakeHttpResponse(
            {
                "data": {
                    "id": "gen-123",
                    "status": "succeeded",
                    "outputs": [{"url": "https://media.example/result.png", "mime": "image/png"}],
                }
            }
        )


@pytest.fixture
def make(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)

    def _make(*, max_attempts=1):
        adapter = Vidilab(api_key="vidilab-test-key", config=ClientConfig(max_attempts=max_attempts, poll_interval=0))
        pool = FakePool()
        monkeypatch.setattr(adapter.resources, "pool", pool)
        return adapter, pool

    return _make


def _body(call):
    return json.loads(call["body"])


def test_sync_text_to_image_polls_and_normalizes_output(make):
    adapter, pool = make()
    pool.status_responses = [
        {"data": {"id": "gen-123", "status": "running"}},
        {
            "data": {
                "id": "gen-123",
                "status": "succeeded",
                "outputs": [{"url": "https://media.example/result.png"}],
            }
        },
    ]

    response = adapter.submit("nano-banana-2", prompt="A red fox on a snowy ridge", workflow="t2i")

    assert response.status == "completed"
    assert response.media_url == "https://media.example/result.png"
    assert pool.calls[0]["url"] == "https://vidlab.ai/v1/generations"
    assert pool.calls[0]["headers"]["Authorization"] == "Bearer vidilab-test-key"
    assert pool.calls[0]["headers"]["Idempotency-Key"]
    assert _body(pool.calls[0]) == {
        "model": "nano-banana-2",
        "input": {"prompt": "A red fox on a snowy ridge"},
    }


def test_local_image_is_uploaded_before_image_to_image(make, tmp_path):
    adapter, pool = make()
    image_path = tmp_path / "input.jpg"
    image_path.write_bytes(b"jpeg-data")

    response = adapter.submit("gpt-image-2", "Turn the scene into a watercolor", image=image_path, workflow="i2i")

    assert response.status == "completed"
    upload, generation, _status = pool.calls
    assert upload["url"] == "https://vidlab.ai/v1/uploads"
    assert upload["body"] == b"jpeg-data"
    assert upload["headers"]["Content-Type"] == "image/jpeg"
    assert upload["headers"]["X-File-Name"] == "input.jpg"
    assert _body(generation)["input"]["images"] == ["https://upload.example/image.jpg"]


def test_async_submission_sends_webhook_and_returns_queued(make):
    adapter, pool = make()

    response = adapter.submit_async(
        "wan-3.0",
        webhook="https://example.test/vidilab-callback",
        prompt="A boat crossing a calm lake",
        workflow="t2v",
        duration=5,
    )

    assert response.status == "queued"
    assert response.request_id == "gen-123"
    assert _body(pool.calls[0]) == {
        "model": "wan-3.0",
        "input": {"prompt": "A boat crossing a calm lake", "duration": 5},
        "webhook_url": "https://example.test/vidilab-callback",
    }


def test_video_input_and_cancellation_are_rejected(make):
    adapter, pool = make()

    with pytest.raises(CapabilityError, match="video-to-video"):
        adapter.submit("wan-3.0", "x", video="https://example.test/input.mp4", workflow="v2v")
    with pytest.raises(CapabilityError, match="cancellation"):
        adapter.cancel("gen-123")
    assert pool.calls == []


def test_provider_http_errors_are_reported(make):
    adapter, pool = make()
    pool.request = lambda *args, **kwargs: FakeHttpResponse(
        {"error": {"message": "invalid model"}}, status=422
    )

    with pytest.raises(HttpProviderError, match="invalid model"):
        adapter.submit("not-a-model", prompt="A prompt", workflow="t2i")


def test_generation_status_wait_is_bounded(make):
    adapter, pool = make()

    with pytest.raises(ValueError, match="between 0 and 60"):
        adapter.status("gen-123", wait=61)
    assert pool.calls == []
