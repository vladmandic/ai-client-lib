"""PixVerse video generation adapter.

Endpoints (https://docs.platform.pixverse.ai/, verified 2026-11-21), all under
`https://app-api.pixverse.ai/openapi/v2`:

    workflow             endpoint                        model names (e.g.)
    text-to-video        POST /video/text/generate       c1, c1/text-to-video
    image-to-video       POST /video/img/generate        c1/image-to-video
    transition           POST /video/transition/generate c1/transition
    reference-to-video   POST /video/fusion/generate     c1/reference-to-video (alias c1/fusion)
    status               GET  /video/result/{video_id}
    image upload         POST /image/upload              multipart `image` or `image_url`

The model id sent to PixVerse is the part before the workflow token
(`c1/reference-to-video` sends `model: "c1"`).

Raw workflow (what srv/gateway.py uses): `input` is the PixVerse body verbatim,
plus URL conveniences so callers never manage PixVerse image ids themselves:
    image-to-video      `image_url`                    -> `img_id`
    transition          `first_frame_url`/`last_frame_url` -> `first_frame_img`/`last_frame_img`
    reference-to-video  `image_references[].image_url` -> `image_references[].img_id`
Each URL is uploaded with POST /image/upload (`image_url` field) on the same key
that then submits, because PixVerse ids only work on the account that made them.

Async: PixVerse calls back a webhook registered in its console
(platform.pixverse.ai/webhook), referenced per request by `webhook_id`, not by a
URL. `submit_async` therefore needs a `webhook_id` (kwarg, constructor or
PIXVERSE_WEBHOOK_ID); the `webhook` URL argument cannot be sent and is ignored.
Callbacks are signed: see `verify_webhook_signature`.
"""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import base64
import hashlib
import hmac
import mimetypes
import os
import time
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

from urllib3.filepost import encode_multipart_formdata

from .core import (
    RAW_WORKFLOW,
    CapabilityError,
    ClientConfig,
    HttpProviderError,
    ProviderHttpClient,
    Response,
    extract_media_urls,
    validate_workflow_inputs,
)

# Workflow token in a model name -> PixVerse endpoint (under /video/).
ENDPOINTS: dict[str, str] = {
    "text-to-video": "text/generate",
    "image-to-video": "img/generate",
    "transition": "transition/generate",
    "reference-to-video": "fusion/generate",
}
WORKFLOW_TOKENS: dict[str, str] = {
    "text-to-video": "text-to-video",
    "image-to-video": "image-to-video",
    "transition": "transition",
    "first-last-frame": "transition",
    "reference-to-video": "reference-to-video",
    "fusion": "reference-to-video",
}

# Task status codes (GET /video/result): 1 done, 5 generating, 7 moderation, 8 failed.
STATUS_MAP = {1: "completed", 5: "processing", 7: "failed", 8: "failed"}
STATUS_ERRORS = {7: "PixVerse content moderation failed", 8: "PixVerse generation failed"}

# ErrCode (non-zero even on HTTP 200) -> the HTTP status the gateway reports, so
# callers branch the same way they do for fal / KIE: 401 and 402 are account
# errors (the gateway fails over to another key), 404 is "not this key's
# request", 422 is bad input or moderation, 429 is back off and retry.
_AUTH_CODES = {10001, 10002, 10003, 10004, 10005, 400009, 500020, 500307}
_BALANCE_CODES = {500090}
_NOT_FOUND_CODES = {500008, 500085, 701009}
_BUSY_CODES = {500044, 500069, 712008}
_BAD_INPUT_CODES = {
    400011, 400013, 400017, 400018, 400019, 400032, 500030, 500031, 500032, 500033,
    500041, 500042, 500047, 500052, 500054, 500058, 500063, 500111, 701001, 701002,
    4000012,
}


_ERRCODE_HTTP_STATUS = {
    **{code: 401 for code in _AUTH_CODES},
    **{code: 402 for code in _BALANCE_CODES},
    **{code: 404 for code in _NOT_FOUND_CODES},
    **{code: 429 for code in _BUSY_CODES},
    **{code: 422 for code in _BAD_INPUT_CODES},
}


def errcode_status(code: Any) -> int:
    """HTTP status to report for a PixVerse ErrCode (unknown 4xxxxx = bad input, else 502)."""
    try:
        code = int(code)
    except (TypeError, ValueError):
        return 502
    default = 422 if 400000 <= code < 500000 else 502
    return _ERRCODE_HTTP_STATUS.get(code, default)


def signing_payload(payload: dict[str, Any]) -> str:
    """The `url_encoded_payload` part of a PixVerse webhook signing string.

    Fields sorted by key, booleans as lowercase `true`/`false`, everything else
    `str()`, encoded as a query string with no safe characters (PixVerse's own
    Python example).
    """
    return urlencode(
        {key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in sorted(payload.items())},
        safe="",
    )


def verify_webhook_signature(
    secret_key: str,
    timestamp: str,
    nonce: str,
    payload: dict[str, Any],
    signature: str,
    *,
    max_age_sec: float | None = 300,
    now: float | None = None,
) -> bool:
    """Check a PixVerse callback's `Webhook-Signature` header.

    `timestamp`, `nonce` and `signature` are the Webhook-Timestamp,
    Webhook-Nonce and Webhook-Signature headers; `payload` is the decoded JSON
    body. Signature = base64(HMAC-SHA256(secret, "{timestamp}\\n{nonce}\\n{payload}")).
    Timestamps older or newer than `max_age_sec` are rejected (replay guard;
    None disables it). The receiver must answer HTTP 200 with body `ok`.
    """
    if max_age_sec is not None:
        try:
            age = abs((time.time() if now is None else now) - float(timestamp))
        except (TypeError, ValueError):
            return False
        if age > max_age_sec:
            return False
    signing_string = f"{timestamp}\n{nonce}\n{signing_payload(payload)}"
    expected = base64.b64encode(
        hmac.new(secret_key.encode("utf-8"), signing_string.encode("utf-8"), hashlib.sha256).digest()
    ).decode("ascii")
    return hmac.compare_digest(expected, signature or "")


def split_model(model: str) -> tuple[str, str | None]:
    """`c1/reference-to-video` -> ("c1", "reference-to-video"); `c1` -> ("c1", None)."""
    head, sep, tail = model.rpartition("/")
    if sep and tail in WORKFLOW_TOKENS:
        return head, WORKFLOW_TOKENS[tail]
    return model, None


class Pixverse(ProviderHttpClient):
    """Client for PixVerse text, image, transition and reference (fusion) video APIs."""

    base_url = "https://app-api.pixverse.ai/openapi/v2"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
        webhook_id: str | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("PIXVERSE_API_KEY")
        if key is None:
            raise ValueError("api_key or PIXVERSE_API_KEY is required")
        super().__init__("pixverse", key, config)
        self.webhook_id = webhook_id if webhook_id is not None else os.environ.get("PIXVERSE_WEBHOOK_ID")

    def submit(
        self,
        model: str,
        prompt: str | None = None,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit")
        api_key = self._key_for_request()
        trace_id = str(uuid4())
        workflow, body = self._build(model, prompt, image, video, workflow, kwargs, api_key, record.correlation_id)
        body.pop("webhook_id", None)  # polled: PixVerse says omit it
        response = self._request(workflow, body, api_key, trace_id, record.correlation_id, "submit")
        request_id = self._video_id(response)
        self.resources.stats.update(record.correlation_id, request_id=request_id, status="queued")
        return self._poll(request_id, api_key, trace_id, record.correlation_id, raw_request=body)

    def submit_async(
        self,
        model: str,
        webhook: str | None = None,
        prompt: str | None = None,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        **kwargs: Any,
    ) -> Response:
        """Queue a generation; PixVerse calls the console-registered webhook `webhook_id`.

        `webhook` (a URL) is accepted for interface parity but PixVerse cannot
        take one per request: the callback URL is the one registered for
        `webhook_id` in the PixVerse console.
        """
        del webhook
        webhook_id = kwargs.pop("webhook_id", None) or self.webhook_id
        if not webhook_id:
            raise CapabilityError(
                "PixVerse callbacks need a webhook_id registered at platform.pixverse.ai/webhook "
                "(pass webhook_id or set PIXVERSE_WEBHOOK_ID)"
            )
        record = self.resources.stats.start("submit_async")
        api_key = self._key_for_request()
        trace_id = str(uuid4())
        workflow, body = self._build(model, prompt, image, video, workflow, kwargs, api_key, record.correlation_id)
        body["webhook_id"] = str(webhook_id)
        response = self._request(workflow, body, api_key, trace_id, record.correlation_id, "submit_async")
        request_id = self._video_id(response)
        self.resources.stats.update(record.correlation_id, request_id=request_id, status="queued")
        return self._normalize(response, record.correlation_id, "queued", request_id, raw_request=body)

    def status(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._status_request(request_id, self._key_for_request(), str(uuid4()), record.correlation_id)
        status = self._status(response)
        self.resources.stats.update(record.correlation_id, status=status, finish=status in {"completed", "failed"})
        return self._normalize(response, record.correlation_id, status, request_id)

    def cancel(self, request_id: str) -> Response:
        del request_id
        raise CapabilityError("PixVerse cancellation is not documented")

    def upload_image_url(self, image_url: str, api_key: str | None = None, correlation_id: str | None = None) -> int:
        """Register a remote image with PixVerse (POST /image/upload, `image_url`) and return its img_id.

        The URL must serve image/jpeg, image/png or image/webp (not
        application/octet-stream), under 20 MB and 10,000 px per side.
        """
        return self._upload({"image_url": image_url}, api_key, correlation_id)

    def upload_image_file(self, path: str | os.PathLike[str], api_key: str | None = None,
                          correlation_id: str | None = None) -> int:
        """Upload a local image (POST /image/upload, multipart `image`) and return its img_id."""
        path = os.fspath(path)
        with open(path, "rb") as media_file:
            data = media_file.read()
        content_type = mimetypes.guess_type(path)[0] or "image/png"
        return self._upload({"image": (os.path.basename(path), data, content_type)}, api_key, correlation_id)

    # ── request building ─────────────────────────────────────────────────────

    def _build(
        self,
        model: str,
        prompt: str | None,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        workflow: str | None,
        kwargs: dict[str, Any],
        api_key: str,
        correlation_id: str,
    ) -> tuple[str, dict[str, Any]]:
        """Resolve the PixVerse workflow and request body (uploading any image URLs)."""
        if video is not None:
            raise CapabilityError("PixVerse video-to-video is not supported by this adapter")
        model_id, token = split_model(model)
        if workflow == RAW_WORKFLOW:
            if token is None:
                raise CapabilityError(
                    "PixVerse raw requests name the workflow in the model, e.g. c1/image-to-video, "
                    f"c1/transition or c1/reference-to-video (got {model!r})"
                )
            workflow = token
        elif workflow in WORKFLOW_TOKENS or token is not None:
            workflow = WORKFLOW_TOKENS.get(workflow or "", token)
        else:
            workflow = validate_workflow_inputs(model, image, video, workflow)
            workflow = {"text-to-image": "text-to-video", "image-to-image": "image-to-video"}.get(workflow, workflow)
        if workflow not in ENDPOINTS:
            raise CapabilityError(f"PixVerse does not support workflow {workflow!r}")

        body: dict[str, Any] = {"model": model_id, **kwargs}
        if prompt is not None:
            body["prompt"] = prompt

        def img_id(url: Any) -> int:
            return self.upload_image_url(str(url), api_key, correlation_id)

        if workflow == "text-to-video":
            body.setdefault("aspect_ratio", "16:9")
            body.setdefault("duration", 5)
            body.setdefault("quality", "540p")
        elif workflow == "image-to-video":
            url = body.pop("image_url", None) or image
            if "img_id" not in body:
                if url is None:
                    raise CapabilityError("PixVerse image-to-video requires an image, image_url or img_id")
                body["img_id"] = self._image_id(url, api_key, correlation_id)
            body.setdefault("duration", 5)
            body.setdefault("quality", "540p")
        elif workflow == "transition":
            for url_key, id_key in (("first_frame_url", "first_frame_img"), ("last_frame_url", "last_frame_img")):
                url = body.pop(url_key, None)
                if id_key not in body:
                    if url is None:
                        raise CapabilityError(f"PixVerse transition requires {id_key} or {url_key}")
                    body[id_key] = img_id(url)
        else:  # reference-to-video (fusion)
            refs = body.get("image_references")
            if not isinstance(refs, list) or not refs:
                raise CapabilityError("PixVerse reference-to-video requires image_references (1-10 items)")
            resolved = []
            for ref in refs:
                ref = dict(ref)
                url = ref.pop("image_url", None)
                if "img_id" not in ref:
                    if url is None:
                        raise CapabilityError("each PixVerse image reference needs img_id or image_url")
                    ref["img_id"] = img_id(url)
                resolved.append(ref)
            body["image_references"] = resolved
        return workflow, body

    def _image_id(self, image: str | os.PathLike[str], api_key: str, correlation_id: str) -> int:
        value = str(image)
        if value.startswith(("http://", "https://")):
            return self.upload_image_url(value, api_key, correlation_id)
        return self.upload_image_file(value, api_key, correlation_id)

    # ── HTTP ────────────────────────────────────────────────────────────────

    def _poll(
        self,
        request_id: str,
        api_key: str,
        trace_id: str,
        correlation_id: str,
        raw_request: Any = None,
    ) -> Response:
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self._status_request(request_id, api_key, trace_id, correlation_id)
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status in {"completed", "failed"}:
                self.resources.stats.update(correlation_id, status=status, finish=True)
                return self._normalize(response, correlation_id, status, request_id, raw_request=raw_request)
            time.sleep(self.config.poll_interval)
        self.resources.stats.update(correlation_id, error="polling timeout")
        raise TimeoutError(f"PixVerse video {request_id} polling timed out")

    def _request(
        self,
        workflow: str,
        body: dict[str, Any],
        api_key: str,
        trace_id: str,
        correlation_id: str,
        operation: str,
    ) -> Any:
        status_code, response = self.request_json(
            "POST",
            f"{self.base_url}/video/{ENDPOINTS[workflow]}",
            body=body,
            headers=self._headers(api_key, trace_id),
            correlation_id=correlation_id,
            operation=operation,
        )
        return self._checked(status_code, response)

    def _status_request(self, request_id: str, api_key: str, trace_id: str, correlation_id: str) -> Any:
        status_code, response = self.request_json(
            "GET",
            f"{self.base_url}/video/result/{request_id}",
            body=None,
            headers=self._headers(api_key, trace_id),
            correlation_id=correlation_id,
            operation="status",
        )
        return self._checked(status_code, response)

    def _upload(self, fields: dict[str, Any], api_key: str | None, correlation_id: str | None) -> int:
        del correlation_id  # uploads are not tracked as generation records
        body, content_type = encode_multipart_formdata(fields)
        headers = {
            "API-KEY": api_key or self._key_for_request(),
            "Ai-trace-id": str(uuid4()),
            "Content-Type": content_type,
        }
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            response = self.resources.pool.request(
                "POST", f"{self.base_url}/image/upload", body=body, headers=headers, preload_content=True
            )
            data = self._decode(response)
        finally:
            self.resources.stats.end_http()
            self.resources.release()
        if response.status >= 400:
            raise HttpProviderError(response.status, f"PixVerse image upload failed: {self._error_message(data)}",
                                    raw_response=data)
        data = self._checked(response.status, data)
        try:
            return int(data["Resp"]["img_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise HttpProviderError(502, "PixVerse upload response did not include Resp.img_id",
                                    raw_response=data) from error

    @staticmethod
    def _checked(status_code: int, response: Any) -> Any:
        """PixVerse reports most errors as HTTP 200 with a non-zero ErrCode."""
        if isinstance(response, dict):
            code = response.get("ErrCode")
            if code not in (None, 0, "0"):
                message = response.get("ErrMsg") or "PixVerse request failed"
                raise HttpProviderError(errcode_status(code), f"PixVerse ErrCode {code}: {message}",
                                        raw_response=response)
        elif status_code < 400:
            raise HttpProviderError(502, "PixVerse returned a non-JSON response", raw_response=response)
        return response

    @staticmethod
    def _headers(api_key: str, trace_id: str) -> dict[str, str]:
        return {"API-KEY": api_key, "Ai-trace-id": trace_id, "Content-Type": "application/json"}

    # ── response parsing ────────────────────────────────────────────────────

    @staticmethod
    def _video_id(response: Any) -> str:
        try:
            return str(response["Resp"]["video_id"])
        except (KeyError, TypeError) as error:
            raise HttpProviderError(502, "PixVerse response did not include Resp.video_id",
                                    raw_response=response) from error

    @staticmethod
    def _status(response: Any) -> str:
        try:
            value = int(response["Resp"]["status"])
        except (KeyError, TypeError, ValueError):
            return "failed"
        status = STATUS_MAP.get(value, "processing")
        # Only done once the output URL exists (PixVerse: status 1 AND Resp.url).
        if status == "completed" and not response["Resp"].get("url"):
            return "processing"
        return status

    @classmethod
    def _extract_media_url(cls, result: Any, response: Any) -> str | list[str] | None:
        urls: list[str] = []
        if isinstance(result, dict) and result.get("url"):
            urls.append(str(result["url"]))
        if not urls and result is not None:
            urls.extend(extract_media_urls(result))
        if not urls and response is not None:
            urls.extend(extract_media_urls(response))
        if not urls:
            return None
        return urls[0] if len(urls) == 1 else urls

    @classmethod
    def _normalize(
        cls,
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str,
        raw_request: Any = None,
    ) -> Response:
        resp = response.get("Resp") if isinstance(response, dict) else None
        error = None
        if status == "failed":
            code = resp.get("status") if isinstance(resp, dict) else None
            error = STATUS_ERRORS.get(code) or "PixVerse generation failed"
        result = resp if status == "completed" else None
        media_url = cls._extract_media_url(result, response) if status == "completed" else None
        return Response(
            request_id=request_id,
            status=status,
            result=result,
            error=error,
            raw_response=response,
            correlation_id=correlation_id,
            raw_request=raw_request,
            media_url=media_url,
        )
