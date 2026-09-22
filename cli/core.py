"""Shared infrastructure for provider clients."""

# Shared pools and semaphores are intentionally long-lived resources.
# pylint: disable=consider-using-with

from __future__ import annotations

import base64
import io
import json
import mimetypes
import os
import random
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Self
from uuid import uuid4

import urllib3
from PIL import Image

from srv.logger import log

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
RETRYABLE_STATUS_CODES = {408, 429}
WORKFLOW_ALIASES = {
    "t2i": "text-to-image",
    "i2i": "image-to-image",
    "t2v": "text-to-video",
    "i2v": "image-to-video",
    "v2v": "video-to-video",
}


class ProviderError(RuntimeError):
    """Base error for provider client failures."""


class CapabilityError(ProviderError):
    """Raised when a provider does not support an operation."""


def infer_workflow(
    model: str,
    has_image: bool = False,
    has_video: bool = False,
    workflow: str | None = None,
) -> str:
    """Infer a generation workflow from a model identifier."""
    if workflow is not None:
        workflow = WORKFLOW_ALIASES.get(workflow, workflow)
        if workflow not in {
            "text-to-image",
            "image-to-image",
            "edit",
            "text-to-video",
            "image-to-video",
            "video-to-video",
        }:
            raise CapabilityError(f"unsupported workflow: {workflow}")
        return workflow
    normalized = re.sub(r"[_/]+", "-", model.lower())
    for detected_workflow in (
        "text-to-image",
        "image-to-image",
        "text-to-video",
        "image-to-video",
        "video-to-video",
    ):
        if detected_workflow in normalized:
            return detected_workflow
    if "edit" in normalized:
        return "edit"
    if has_video:
        return "video-to-video"
    if has_image:
        return "image-to-image"
    return "text-to-image"


def validate_workflow_inputs(
    model: str,
    image: str | os.PathLike[str] | None,
    video: str | os.PathLike[str] | None,
    workflow: str | None = None,
) -> str:
    """Validate standard media inputs against the model-name workflow."""
    selected_workflow = infer_workflow(
        model,
        image is not None,
        video is not None,
        workflow,
    )
    requires_image = selected_workflow in {"image-to-image", "image-to-video", "edit"}
    requires_video = selected_workflow == "video-to-video"
    if requires_image and (image is None or video is not None):
        raise CapabilityError(f"{selected_workflow} workflow requires an image and no video")
    if requires_video and (video is None or image is not None):
        raise CapabilityError("video-to-video model requires a video and no image")
    if selected_workflow in {"text-to-image", "text-to-video"} and (image is not None or video is not None):
        raise CapabilityError(f"{selected_workflow} workflow does not accept image or video input")
    return selected_workflow


class HttpProviderError(ProviderError):
    """Raised for a non-successful provider HTTP response."""

    def __init__(self, status_code: int, message: str, raw_response: Any = None):
        super().__init__(f"{status_code}: {message}" if message else str(status_code))
        self.status_code = status_code
        self.raw_response = raw_response


@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Shared polling, retry, cleanup, and rate-limit configuration."""

    poll_timeout: float = 600.0
    poll_interval: float = 2.0
    max_attempts: int = 3
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_jitter: float = 1.0
    cleanup_uploaded_media: bool = False
    concurrency_limit: int | None = None
    requests_per_second: float | None = None
    media_strategy: str = "auto"
    data_uri_max_bytes: int = 10 * 1024 * 1024

    def __str__(self) -> str:
        return f'ClientConfig(poll_timeout={self.poll_timeout} poll_interval={self.poll_interval} max_attempts={self.max_attempts} retry_initial_delay={self.retry_initial_delay} retry_max_delay={self.retry_max_delay} retry_jitter={self.retry_jitter} cleanup_uploaded_media={self.cleanup_uploaded_media} concurrency_limit={self.concurrency_limit} requests_per_second={self.requests_per_second} media_strategy="{self.media_strategy}" data_uri_max_bytes={self.data_uri_max_bytes})'


class BytesList(list[bytes]):
    """List of bytes for media items with callable getter support."""

    def __call__(self) -> BytesList:
        return self


class ImagesList(list[Any]):
    """List of PIL Images with callable getter support."""

    def __call__(self) -> ImagesList:
        return self


def extract_media_urls(value: Any) -> list[str]:
    """Recursively extract media URLs from a provider result or response."""
    urls: list[str] = []

    def _walk(val: Any) -> None:
        if isinstance(val, str):
            if val.startswith(("http://", "https://", "oss://", "data:")) and val not in urls:
                urls.append(val)
        elif isinstance(val, dict):
            for key in (
                "resultUrls",
                "images",
                "data",
                "content",
                "Resp",
                "response",
                "url",
                "video_url",
                "image_url",
                "fileUrl",
                "resultUrl",
            ):
                if key in val:
                    _walk(val[key])
            for k, v in val.items():
                if k in {
                    "param",
                    "paramJson",
                    "raw_request",
                    "callBackUrl",
                    "callback_url",
                    "webhook",
                    "webhook_url",
                    "input",
                }:
                    continue
                if k not in (
                    "resultUrls",
                    "images",
                    "data",
                    "content",
                    "Resp",
                    "response",
                    "url",
                    "video_url",
                    "image_url",
                    "fileUrl",
                    "resultUrl",
                ):
                    _walk(v)
        elif isinstance(val, (list, tuple)):
            for item in val:
                _walk(item)

    _walk(value)
    return urls


def _fetch_media_bytes(pool: urllib3.PoolManager, url: str) -> bytes | None:
    if url.startswith("data:"):
        if "," in url:
            _, encoded = url.split(",", 1)
            return base64.b64decode(encoded)
        return None
    if url.startswith(("http://", "https://")):
        resp = pool.request("GET", url, preload_content=True)
        if resp.status >= 400:
            raise HttpProviderError(resp.status, f"Failed to fetch media from {url}")
        return resp.data
    return None


@dataclass(slots=True)
class Response:
    """Provider-independent response fields plus the raw response."""

    request_id: str | None
    correlation_id: str | None = None
    status: str | None = None
    result: Any = None
    error: str | None = None
    raw_request: Any = None
    raw_response: Any = None
    media_url: str | list[str] | None = None
    _cached_bytes: BytesList | None = field(default=None, init=False, repr=False)
    _cached_images: ImagesList | None = field(default=None, init=False, repr=False)

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values.pop("_cached_bytes", None)
        values.pop("_cached_images", None)
        return values

    def __str__(self) -> str:
        return f'Response(id="{self.request_id}" status="{self.status}" error="{self.error}" media="{self.media_url}" result="{self.result}")'

    @property
    def media_urls(self) -> list[str]:
        """Return all media URLs as a list of strings."""
        if self.media_url is None:
            return []
        if isinstance(self.media_url, str):
            return [self.media_url]
        return list(self.media_url)

    @property
    def bytes(self) -> BytesList:
        """Fetch media URL(s) and return content as a list of bytes per item."""
        if self._cached_bytes is not None:
            return self._cached_bytes
        items: list[bytes] = []
        urls = self.media_urls
        if urls:
            pool = urllib3.PoolManager()
            try:
                for url in urls:
                    try:
                        data = _fetch_media_bytes(pool, url)
                        if data is not None:
                            items.append(data)
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass
            finally:
                pool.clear()
        self._cached_bytes = BytesList(items)
        return self._cached_bytes

    @property
    def images(self) -> ImagesList:
        """Convert fetched media bytes to PIL Images and return as a list."""
        if self._cached_images is not None:
            return self._cached_images
        image_items: list[Any] = []
        for raw_bytes in self.bytes:
            try:
                img = Image.open(io.BytesIO(raw_bytes))
                img.load()
                image_items.append(img)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        self._cached_images = ImagesList(image_items)
        return self._cached_images


@dataclass(slots=True)
class RequestRecord:
    """Statistics for one logical generation job."""

    correlation_id: str
    operation: str
    request_id: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str | None = None
    status: str = "queued"
    http_status: int | None = None
    attempts: int = 0
    latency: float | None = None
    error: str | None = None
    _started_monotonic: float = field(default_factory=time.monotonic, repr=False)

    def finish(self, status: str | None = None) -> None:
        if status is not None:
            self.status = status
        self.ended_at = datetime.now(UTC).isoformat()
        self.latency = time.monotonic() - self._started_monotonic

    def as_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values.pop("_started_monotonic", None)
        return values


class ProviderStats:
    """Thread-safe, process-local statistics for one provider."""

    def __init__(self, provider: str):
        self.provider = provider
        self._records: dict[str, RequestRecord] = {}
        self._lock = threading.RLock()
        self._active_http = 0

    def start(self, operation: str) -> RequestRecord:
        record = RequestRecord(correlation_id=str(uuid4()), operation=operation)
        with self._lock:
            self._records[record.correlation_id] = record
        return record

    def update(
        self,
        correlation_id: str,
        *,
        request_id: str | None = None,
        status: str | None = None,
        http_status: int | None = None,
        error: str | None = None,
        finish: bool = False,
    ) -> None:
        with self._lock:
            record = self._records[correlation_id]
            if request_id is not None:
                record.request_id = request_id
            if status is not None:
                record.status = status
            if http_status is not None:
                record.http_status = http_status
            if error is not None:
                record.error = error
            if finish or record.status in TERMINAL_STATUSES:
                record.finish()

    def record_attempt(self, correlation_id: str, status_code: int | None = None) -> None:
        with self._lock:
            record = self._records.get(correlation_id)
            if record is not None:
                record.attempts += 1
                if status_code is not None:
                    record.http_status = status_code

    def begin_http(self) -> None:
        with self._lock:
            self._active_http += 1

    def end_http(self) -> None:
        with self._lock:
            self._active_http = max(0, self._active_http - 1)

    def records(self) -> list[dict[str, Any]]:
        with self._lock:
            return [record.as_dict() for record in self._records.values()]

    def find_by_request_id(self, request_id: str) -> RequestRecord | None:
        with self._lock:
            return next(
                (record for record in self._records.values() if record.request_id == request_id),
                None,
            )

    def current_requests(self) -> int:
        with self._lock:
            return sum(
                record.status in {"queued", "processing"}
                for record in self._records.values()
            )

    def active_http_requests(self) -> int:
        with self._lock:
            return self._active_http

    def close(self) -> None:
        with self._lock:
            self._records.clear()


class ProviderResources:
    """Shared pool, limiter, and statistics resources for one provider."""

    def __init__(self, provider: str, config: ClientConfig):
        self.provider = provider
        self.pool = urllib3.PoolManager()  # pylint: disable=consider-using-with
        self.stats = ProviderStats(provider)
        self._semaphore = (
            threading.BoundedSemaphore(config.concurrency_limit)  # pylint: disable=consider-using-with
            if config.concurrency_limit is not None
            else None
        )
        self._last_request = 0.0
        self._rate_lock = threading.Lock()

    def acquire(self) -> None:
        if self._semaphore is not None:
            self._semaphore.acquire()

    def release(self) -> None:
        if self._semaphore is not None:
            self._semaphore.release()

    def rate_limit(self, requests_per_second: float | None) -> None:
        if requests_per_second is None or requests_per_second <= 0:
            return
        interval = 1.0 / requests_per_second
        with self._rate_lock:
            wait = interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def close(self) -> None:
        self.pool.clear()
        self.stats.close()


class ProviderPoolRegistry:
    """Process-local registry that shares one resource set per provider."""

    _lock = threading.RLock()
    _resources: dict[str, ProviderResources] = {}
    _references: dict[str, int] = {}

    @classmethod
    def acquire(cls, provider: str, config: ClientConfig) -> ProviderResources:
        with cls._lock:
            if provider not in cls._resources:
                cls._resources[provider] = ProviderResources(provider, config)
                cls._references[provider] = 0
            cls._references[provider] += 1
            return cls._resources[provider]

    @classmethod
    def release(cls, provider: str) -> None:
        with cls._lock:
            if provider not in cls._references:
                return
            cls._references[provider] -= 1
            if cls._references[provider] <= 0:
                cls._resources.pop(provider).close()
                cls._references.pop(provider)

    @classmethod
    def close_all(cls) -> None:
        with cls._lock:
            for resource in cls._resources.values():
                resource.close()
            cls._resources.clear()
            cls._references.clear()

    @classmethod
    def stats(cls, provider: str) -> ProviderStats | None:
        with cls._lock:
            resource = cls._resources.get(provider)
            return resource.stats if resource is not None else None


class ProviderHttpClient:
    """Shared HTTP behavior used by provider adapters."""

    def __init__(
        self,
        provider: str,
        api_key: str | list[str],
        config: ClientConfig | None = None,
    ):
        self.provider = provider
        self.api_keys = self._validate_api_keys(api_key)
        self.config = config or ClientConfig()
        self.resources = ProviderPoolRegistry.acquire(provider, self.config)
        self._closed = False

    def __str__(self) -> str:
        return f'Client(provider={self.provider} config={self.config})'

    @staticmethod
    def _validate_api_keys(api_key: str | list[str]) -> tuple[str, ...]:
        keys = (api_key,) if isinstance(api_key, str) else tuple(api_key)
        if not keys or any(not isinstance(key, str) or not key for key in keys):
            raise ValueError("api_key must be a non-empty string or list of strings")
        return keys

    def _key_for_request(self) -> str:
        return random.choice(self.api_keys)

    def prepare_media(self, media: str | os.PathLike[str] | None) -> str | None:
        """Return a provider-ready URL or data URI for one media input."""
        if media is None:
            return None
        value = str(media)
        if value.startswith(("http://", "https://", "data:")):
            return value
        if self.config.media_strategy == "upload":
            raise CapabilityError("raw provider upload is not implemented")
        path = os.fspath(media)
        size = os.path.getsize(path)
        if size > self.config.data_uri_max_bytes:
            raise CapabilityError(
                f"local media exceeds data URI limit ({self.config.data_uri_max_bytes} bytes)"
            )
        if self.config.media_strategy not in {"auto", "data_uri"}:
            raise ValueError("media_strategy must be auto, data_uri, or upload")
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as media_file:
            encoded = base64.b64encode(media_file.read()).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    def headers(self, correlation_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._key_for_request()}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
        }

    def request_json(
        self,
        method: str,
        url: str,
        *,
        body: dict[str, Any] | None,
        headers: dict[str, str],
        correlation_id: str,
        operation: str,
    ) -> tuple[int, Any]:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            for attempt in range(1, self.config.max_attempts + 1):
                self.resources.rate_limit(self.config.requests_per_second)
                try:
                    response = self.resources.pool.request(
                        method,
                        url,
                        body=payload,
                        headers=headers,
                        preload_content=True,
                    )
                    if operation in {"submit", "submit_async"}:
                        self.resources.stats.record_attempt(correlation_id, response.status)
                    data = self._decode(response)
                    if response.status < 400:
                        return response.status, data
                    if not self._retryable(response.status, data) or attempt == self.config.max_attempts:
                        raise HttpProviderError(response.status, self._error_message(data), raw_response=data)
                    self._sleep_before_retry(response, attempt)
                except urllib3.exceptions.HTTPError as error:
                    if operation in {"submit", "submit_async"}:
                        self.resources.stats.record_attempt(correlation_id)
                    if attempt == self.config.max_attempts:
                        raise ProviderError("provider HTTP request failed") from error
                    self._sleep_before_retry(None, attempt)
            raise ProviderError("provider request exhausted retries")
        finally:
            self.resources.stats.end_http()
            self.resources.release()

    @staticmethod
    def _decode(response: urllib3.HTTPResponse) -> Any:
        if not response.data:
            return None
        try:
            return json.loads(response.data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return response.data

    @staticmethod
    def _error_message(data: Any) -> str:
        if isinstance(data, dict):
            detail = data.get("detail")
            if isinstance(detail, list):
                messages = [d.get("msg") or str(d) for d in detail if isinstance(d, dict)]
                if messages:
                    return "; ".join(messages)
            if detail is not None and not isinstance(detail, (dict, list)):
                return str(detail)
            code = data.get("Code") or data.get("code") or data.get("ErrCode") or data.get("err_code")
            for key in (
                "ErrMsg",
                "errMsg",
                "err_msg",
                "error_msg",
                "message",
                "msg",
                "error",
                "errors",
                "error_description",
                "description",
                "detail",
                "details",
            ):
                val = data.get(key)
                if val:
                    if isinstance(val, (dict, list)):
                        try:
                            msg = json.dumps(val)
                        except Exception:
                            msg = str(val)
                    else:
                        msg = str(val)
                    return f"[{code}] {msg}" if code is not None and str(code) not in msg else msg
            if data:
                try:
                    return json.dumps(data)
                except Exception:
                    return str(data)
        elif isinstance(data, str) and data.strip():
            return data.strip()
        elif data is not None:
            return str(data)
        return "provider request failed"

    @staticmethod
    def _retryable(status_code: int, data: Any) -> bool:
        if status_code in RETRYABLE_STATUS_CODES or 500 <= status_code <= 599:
            return True
        if isinstance(data, dict):
            text = str(data).lower()
            return "busy" in text or "temporarily unavailable" in text
        return False

    def _sleep_before_retry(self, response: urllib3.HTTPResponse | None, attempt: int) -> None:
        retry_after = None if response is None else response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                delay = min(float(retry_after), self.config.retry_max_delay)
            except ValueError:
                delay = 0.0
        else:
            limit = min(
                self.config.retry_max_delay,
                self.config.retry_initial_delay * (2 ** (attempt - 1)),
            )
            delay = random.uniform(0.0, limit * self.config.retry_jitter)
        if delay > 0:
            log.debug("provider %s retrying after %.2f seconds", self.provider, delay)
            time.sleep(delay)

    def close(self) -> None:
        if not self._closed:
            ProviderPoolRegistry.release(self.provider)
            self._closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
