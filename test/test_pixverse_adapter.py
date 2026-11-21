"""Unit tests for cli/pixverse.py (no network: a fake urllib3 pool answers every request).

Run: pytest test/test_pixverse_adapter.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest

from cli.core import RAW_WORKFLOW, CapabilityError, ClientConfig, HttpProviderError
from cli.pixverse import (
    Pixverse,
    errcode_status,
    signing_payload,
    split_model,
    verify_webhook_signature,
)

BASE = "https://app-api.pixverse.ai/openapi/v2"


class FakeHttpResponse:
    def __init__(self, data, status=200):
        self.status = status
        self.data = json.dumps(data).encode() if not isinstance(data, bytes) else data
        self.headers = {}


class FakePool:
    """Records requests; answers uploads with increasing img_ids and generates with a video_id."""

    def __init__(self, result_status=1, result_url="https://media.pixverse.ai/out.mp4", generate=None):
        self.calls: list[dict] = []
        self.next_img_id = 100
        self.result_status = result_status
        self.result_url = result_url
        self.generate = generate

    def request(self, method, url, body=None, headers=None, preload_content=True):
        del preload_content
        self.calls.append({"method": method, "url": url, "body": body, "headers": headers or {}})
        if url.endswith("/image/upload"):
            self.next_img_id += 1
            return FakeHttpResponse({"ErrCode": 0, "ErrMsg": "Success",
                                     "Resp": {"img_id": self.next_img_id, "img_url": "https://x/i.png"}})
        if "/video/result/" in url:
            resp = {"id": 42, "status": self.result_status}
            if self.result_url:
                resp["url"] = self.result_url
            return FakeHttpResponse({"ErrCode": 0, "ErrMsg": "Success", "Resp": resp})
        if self.generate is not None:
            return FakeHttpResponse(self.generate)
        return FakeHttpResponse({"ErrCode": 0, "ErrMsg": "Success", "Resp": {"video_id": 42, "credits": 200}})

    def generate_calls(self):
        return [c for c in self.calls if "/generate" in c["url"]]

    def upload_calls(self):
        return [c for c in self.calls if c["url"].endswith("/image/upload")]


@pytest.fixture
def make(monkeypatch):
    def _make(webhook_id="wh-1", **pool_kwargs):
        monkeypatch.delenv("PIXVERSE_WEBHOOK_ID", raising=False)
        adapter = Pixverse(api_key="pv-key", config=ClientConfig(poll_interval=0, max_attempts=1),
                           webhook_id=webhook_id)
        pool = FakePool(**pool_kwargs)
        monkeypatch.setattr(adapter.resources, "pool", pool)
        return adapter, pool
    return _make


def body_of(call):
    return json.loads(call["body"])


def test_split_model():
    assert split_model("c1/reference-to-video") == ("c1", "reference-to-video")
    assert split_model("c1/fusion") == ("c1", "reference-to-video")
    assert split_model("c1/first-last-frame") == ("c1", "transition")
    assert split_model("c1") == ("c1", None)
    assert split_model("v4.5/image-to-video") == ("v4.5", "image-to-video")


def test_raw_image_to_video_uploads_url_then_submits_async(make):
    adapter, pool = make()
    response = adapter.submit_async(
        "c1/image-to-video", "https://ignored.example/hook", workflow=RAW_WORKFLOW,
        prompt="dance", image_url="https://cdn.example/shot.png", duration=3, quality="720p",
    )
    assert response.status == "queued"
    assert response.request_id == "42"
    (upload,) = pool.upload_calls()
    assert b'name="image_url"' in upload["body"] and b"https://cdn.example/shot.png" in upload["body"]
    assert upload["headers"]["API-KEY"] == "pv-key"
    (gen,) = pool.generate_calls()
    assert gen["url"] == f"{BASE}/video/img/generate"
    sent = body_of(gen)
    assert sent == {"model": "c1", "prompt": "dance", "img_id": 101, "duration": 3, "quality": "720p",
                    "webhook_id": "wh-1"}
    assert gen["headers"]["Ai-trace-id"]


def test_raw_reference_to_video_resolves_each_reference(make):
    adapter, pool = make()
    adapter.submit_async(
        "c1/reference-to-video", "https://ignored", workflow=RAW_WORKFLOW,
        prompt="@singer dances in @club", duration=15, quality="720p", aspect_ratio="9:16",
        image_references=[
            {"type": "subject", "ref_name": "singer", "image_url": "https://cdn.example/face.png"},
            {"type": "background", "ref_name": "club", "img_id": 7},
        ],
    )
    assert len(pool.upload_calls()) == 1
    (gen,) = pool.generate_calls()
    assert gen["url"] == f"{BASE}/video/fusion/generate"
    refs = body_of(gen)["image_references"]
    assert refs == [
        {"type": "subject", "ref_name": "singer", "img_id": 101},
        {"type": "background", "ref_name": "club", "img_id": 7},
    ]


def test_raw_transition_resolves_both_frames(make):
    adapter, pool = make()
    adapter.submit_async("c1/transition", None, workflow=RAW_WORKFLOW, prompt="loop", duration=5, quality="720p",
                         first_frame_url="https://a/1.png", last_frame_url="https://a/2.png")
    (gen,) = pool.generate_calls()
    assert gen["url"] == f"{BASE}/video/transition/generate"
    sent = body_of(gen)
    assert (sent["first_frame_img"], sent["last_frame_img"]) == (101, 102)
    assert "first_frame_url" not in sent and "last_frame_url" not in sent


def test_raw_requires_workflow_in_model(make):
    adapter, _ = make()
    with pytest.raises(CapabilityError, match="c1/image-to-video"):
        adapter.submit_async("c1", "https://hook", workflow=RAW_WORKFLOW, prompt="x")


def test_reference_to_video_requires_references(make):
    adapter, _ = make()
    with pytest.raises(CapabilityError, match="image_references"):
        adapter.submit_async("c1/reference-to-video", "https://hook", workflow=RAW_WORKFLOW, prompt="x")


def test_submit_async_without_webhook_id_is_refused(make):
    adapter, pool = make(webhook_id=None)
    with pytest.raises(CapabilityError, match="webhook_id"):
        adapter.submit_async("c1/image-to-video", "https://hook", workflow=RAW_WORKFLOW, prompt="x", img_id=5)
    assert pool.calls == []


def test_webhook_id_kwarg_wins(make):
    adapter, pool = make(webhook_id="default")
    adapter.submit_async("c1/image-to-video", "https://hook", workflow=RAW_WORKFLOW, prompt="x", img_id=5,
                         webhook_id="free")
    assert body_of(pool.generate_calls()[0])["webhook_id"] == "free"


def test_sync_text_to_video_keeps_legacy_shape_and_polls(make):
    adapter, pool = make()
    response = adapter.submit("c1", prompt="android", aspect_ratio="16:9", duration=5, quality="720p",
                              webhook_id="dropped")
    (gen,) = pool.generate_calls()
    assert gen["url"] == f"{BASE}/video/text/generate"
    assert "webhook_id" not in body_of(gen)
    assert response.status == "completed"
    assert response.media_urls == ["https://media.pixverse.ai/out.mp4"]


def test_sync_image_path_uploads_instead_of_requiring_img_id(make):
    adapter, pool = make()
    adapter.submit("c1", prompt="go", image="https://cdn.example/a.png")
    assert len(pool.upload_calls()) == 1
    (gen,) = pool.generate_calls()
    assert gen["url"] == f"{BASE}/video/img/generate"
    assert body_of(gen)["img_id"] == 101


@pytest.mark.parametrize(
    "code,status",
    [(500044, 429), (712008, 429), (400017, 422), (500054, 422), (10005, 401), (500090, 402),
     (500008, 404), (500100, 502)],
)
def test_nonzero_errcode_on_http_200_raises(make, code, status):
    adapter, _ = make(generate={"ErrCode": code, "ErrMsg": "nope", "Resp": None})
    with pytest.raises(HttpProviderError) as raised:
        adapter.submit_async("c1/image-to-video", "https://hook", workflow=RAW_WORKFLOW, prompt="x", img_id=5)
    assert raised.value.status_code == status == errcode_status(code)
    assert f"ErrCode {code}" in str(raised.value)


def test_status_completed_needs_url(make):
    adapter, _ = make(result_status=1, result_url=None)
    assert adapter.status("42").status == "processing"


def test_status_moderation_failure_has_reason(make):
    adapter, _ = make(result_status=7)
    response = adapter.status("42")
    assert response.status == "failed"
    assert response.error == "PixVerse content moderation failed"


def test_status_completed(make):
    adapter, _ = make(result_status=1)
    response = adapter.status("42")
    assert response.status == "completed"
    assert response.media_urls == ["https://media.pixverse.ai/out.mp4"]
    assert response.result["id"] == 42


# ── webhook signatures ──────────────────────────────────────────────────────

DOC_PAYLOAD = {"id": "123456789", "status": 1, "url": "https://example.com/video.mp4", "has_audio": True}


def test_signing_payload_matches_docs_example():
    # Worked example on docs.platform.pixverse.ai/webhook-callbacks.
    assert signing_payload(DOC_PAYLOAD) == "has_audio=true&id=123456789&status=1&url=https%3A%2F%2Fexample.com%2Fvideo.mp4"


def _sign(secret, timestamp, nonce, payload):
    message = f"{timestamp}\n{nonce}\n{signing_payload(payload)}".encode()
    return base64.b64encode(hmac.new(secret.encode(), message, hashlib.sha256).digest()).decode()


def test_verify_webhook_signature():
    ts, nonce = "1763700000", "a" * 32
    sig = _sign("secret", ts, nonce, DOC_PAYLOAD)
    assert verify_webhook_signature("secret", ts, nonce, DOC_PAYLOAD, sig, now=1763700010)
    assert not verify_webhook_signature("other", ts, nonce, DOC_PAYLOAD, sig, now=1763700010)
    assert not verify_webhook_signature("secret", ts, nonce, {**DOC_PAYLOAD, "status": 8}, sig, now=1763700010)
    assert not verify_webhook_signature("secret", ts, nonce, DOC_PAYLOAD, sig, now=1763700000 + 301)
    assert verify_webhook_signature("secret", ts, nonce, DOC_PAYLOAD, sig, max_age_sec=None, now=0)
    assert not verify_webhook_signature("secret", "not-a-number", nonce, DOC_PAYLOAD, sig)
