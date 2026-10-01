"""HTTP gateway exposing the `cli` provider adapters as a Cloud Run service.

Every Echonos caller (backend Cloud Functions, the Next.js API routes) talks to
media providers through this service instead of holding provider keys itself.
Authentication is Cloud Run IAM: the service is deployed private and callers
send a Google-signed ID token, so no request reaching this code is anonymous.

Endpoints (JSON in, JSON out):
    GET  /health
    POST /v1/submit        blocking: submit, poll, return the result
    POST /v1/submit_async  queue with a webhook, return request_id
    POST /v1/status        status, plus the result once completed
    POST /v1/cancel
    POST /v1/upload        raw bytes body -> {"url": ...} (fal CDN)

JSON bodies name the target in `provider` and carry the provider payload
verbatim in `input` (workflow "raw"), so callers keep full control of
model-specific fields such as `image_urls`. `upload` has a raw-bytes body, so
it takes the provider as a `?provider=` query parameter instead.

Keys: `{PROVIDER}_KEYS` (comma-separated) or `{PROVIDER}_KEY`/`{PROVIDER}_API_KEY`.
Each logical request is pinned to ONE key, because fal queue status/result/
cancel only succeed with the key that submitted. Responses carry an opaque
`key_ref` so callers can route follow-up calls back to that key; without it,
follow-ups try every key.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from typing import Any

from anyio import to_thread
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from cli.core import (
    RAW_WORKFLOW,
    CapabilityError,
    ClientConfig,
    HttpProviderError,
    ProviderError,
    Response,
)
from cli.fal import Fal

from .logger import log

# srv.logger only attaches rich handlers when init() runs (the CLI/test server
# path). On Cloud Run, plain stdout lines are what Cloud Logging ingests.
if not log.handlers and not logging.getLogger().handlers:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s %(message)s")
log.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Only fal is wired: it is the only provider Echonos calls today. Adding one is
# an entry here plus its key env var — the adapters already share one interface.
PROVIDERS: dict[str, type] = {"fal": Fal}

# Account-level failures: the KEY is dead (locked, out of balance, revoked),
# not the request. Mirrors Echonos-Backend pipeline_utils/fal_keys.py.
_KEY_ERROR_MARKERS = ("user is locked", "exhausted balance", "unauthorized", "forbidden")
# Status codes meaning "this key cannot see that request" on follow-up calls.
_WRONG_KEY_STATUSES = {401, 403, 404}
_BAD_KEY_TTL_SEC = float(os.environ.get("BAD_KEY_TTL_SEC", "600"))

CONFIG = ClientConfig(
    poll_timeout=float(os.environ.get("POLL_TIMEOUT_SEC", "600")),
    poll_interval=float(os.environ.get("POLL_INTERVAL_SEC", "1")),
    max_records=int(os.environ.get("MAX_STATS_RECORDS", "5000")),
)
# Blocking submits hold a worker thread while polling, so the pool must cover
# the Cloud Run --concurrency setting or requests queue inside the container.
THREAD_LIMIT = int(os.environ.get("THREAD_LIMIT", "80"))


class GatewayError(Exception):
    def __init__(self, status_code: int, message: str, **extra: Any):
        super().__init__(message)
        self.status_code = status_code
        self.extra = extra


def key_ref(key: str) -> str:
    """Stable, non-reversible identifier for a key (safe to store and log)."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def is_key_error(error: Exception) -> bool:
    if isinstance(error, HttpProviderError) and error.status_code == 401:
        return True
    message = str(error).lower()
    return any(marker in message for marker in _KEY_ERROR_MARKERS)


class KeyPool:
    """Configured keys for one provider, with temporary bad-key quarantine."""

    def __init__(self, provider: str, keys: list[str]):
        self.provider = provider
        self.keys = keys
        self._bad: dict[str, float] = {}
        self._adapters: dict[str, Any] = {}
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls, provider: str) -> KeyPool:
        prefix = provider.upper()
        raw = (
            os.environ.get(f"{prefix}_KEYS")
            or os.environ.get(f"{prefix}_KEY")
            or os.environ.get(f"{prefix}_API_KEY")
            or ""
        )
        return cls(provider, [k.strip() for k in raw.split(",") if k.strip()])

    def adapter(self, key: str) -> Any:
        """One long-lived adapter per key, so each carries exactly one key."""
        with self._lock:
            if key not in self._adapters:
                self._adapters[key] = PROVIDERS[self.provider](api_key=key, config=CONFIG)
            return self._adapters[key]

    def healthy(self) -> list[str]:
        if not self.keys:
            raise GatewayError(503, f"no {self.provider} keys configured")
        now = time.monotonic()
        with self._lock:
            healthy = [k for k in self.keys if now - self._bad.get(k, -_BAD_KEY_TTL_SEC) >= _BAD_KEY_TTL_SEC]
        # Every key quarantined: retry them all rather than hard-failing, so a
        # topped-up account recovers without a redeploy.
        return healthy or list(self.keys)

    def mark_bad(self, key: str) -> None:
        with self._lock:
            self._bad[key] = time.monotonic()
        log.error(f"KeyPool(provider={self.provider} key_ref={key_ref(key)} quarantined={_BAD_KEY_TTL_SEC}s)")

    def ordered_for(self, ref: str | None) -> list[str]:
        """All keys, the one matching `ref` first."""
        return sorted(self.keys, key=lambda k: key_ref(k) != ref)


_pools: dict[str, KeyPool] = {}
_pools_lock = threading.Lock()


def pool_for(provider: str) -> KeyPool:
    provider = provider.lower()
    if provider not in PROVIDERS:
        raise GatewayError(404, f"unsupported provider: {provider}")
    with _pools_lock:
        if provider not in _pools:
            _pools[provider] = KeyPool.from_env(provider)
        return _pools[provider]


def serialize(provider: str, model: str, key: str, response: Response) -> dict[str, Any]:
    body = {
        "provider": provider,
        "model": model,
        "request_id": response.request_id,
        "status": response.status,
        "result": response.result,
        "error": response.error,
        "media_urls": response.media_urls,
        "correlation_id": response.correlation_id,
        "key_ref": key_ref(key),
    }
    # result already is the raw response once completed; don't send it twice.
    if response.status != "completed":
        body["raw_response"] = response.raw_response
    return body


def with_failover(pool: KeyPool, call) -> tuple[str, Response]:
    """Run a submission on shuffled healthy keys, moving on only for key errors."""
    keys = pool.healthy()
    random.shuffle(keys)
    last: Exception | None = None
    for key in keys:
        try:
            return key, call(pool.adapter(key))
        except (HttpProviderError, ProviderError) as error:
            if not is_key_error(error):
                raise
            pool.mark_bad(key)
            last = error
    raise GatewayError(503, f"all {len(keys)} {pool.provider} keys failed with account-level errors: {last}")


def on_owning_key(pool: KeyPool, ref: str | None, call) -> tuple[str, Response]:
    """Run a follow-up (status/cancel) on the key that owns the request."""
    if not pool.keys:
        raise GatewayError(503, f"no {pool.provider} keys configured")
    last: Exception | None = None
    for key in pool.ordered_for(ref):
        try:
            return key, call(pool.adapter(key))
        except HttpProviderError as error:
            if error.status_code not in _WRONG_KEY_STATUSES:
                raise
            last = error
    assert last is not None
    raise last


class SubmitBody(BaseModel):
    provider: str
    model: str
    input: dict[str, Any] = Field(default_factory=dict)
    webhook: str | None = None
    headers: dict[str, str] | None = None
    timeout: float | None = Field(default=None, gt=0, le=3600)


class FollowUpBody(BaseModel):
    provider: str
    model: str
    request_id: str
    key_ref: str | None = None


@asynccontextmanager
async def _lifespan(_: FastAPI):
    to_thread.current_default_thread_limiter().total_tokens = THREAD_LIMIT
    for provider in PROVIDERS:
        log.info(f"Gateway(provider={provider} keys={len(pool_for(provider).keys)})")
    yield


app = FastAPI(title="Echonos AI Client Gateway", version="0.1.0", lifespan=_lifespan)


@app.exception_handler(GatewayError)
def _gateway_error(_, error: GatewayError):
    return JSONResponse(status_code=error.status_code, content={"error": str(error), **error.extra})


@app.exception_handler(HttpProviderError)
def _provider_http_error(_, error: HttpProviderError):
    # Keep the provider's status code: callers branch on 422 (bad input) vs 5xx.
    code = error.status_code if 400 <= error.status_code < 600 else 502
    return JSONResponse(
        status_code=code,
        content={"error": str(error), "provider_status": error.status_code, "provider_response": error.raw_response},
    )


@app.exception_handler(CapabilityError)
def _capability_error(_, error: CapabilityError):
    return JSONResponse(status_code=400, content={"error": str(error)})


@app.exception_handler(TimeoutError)
def _timeout_error(_, error: TimeoutError):
    return JSONResponse(status_code=504, content={"error": str(error)})


@app.exception_handler(ProviderError)
def _provider_error(_, error: ProviderError):
    return JSONResponse(status_code=502, content={"error": str(error)})


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "providers": {name: len(pool_for(name).keys) for name in PROVIDERS}}


@app.post("/v1/submit")
def submit(body: SubmitBody) -> dict[str, Any]:
    pool = pool_for(body.provider)

    def call(adapter):
        if body.timeout is not None:
            # Per-call poll deadline needs its own config; the adapter shares
            # the provider's HTTP pool, so this only costs a refcount.
            with PROVIDERS[pool.provider](
                api_key=adapter.api_keys[0], config=replace(CONFIG, poll_timeout=body.timeout)
            ) as scoped:
                return scoped.submit(body.model, workflow=RAW_WORKFLOW, headers=body.headers, **body.input)
        return adapter.submit(body.model, workflow=RAW_WORKFLOW, headers=body.headers, **body.input)

    key, response = with_failover(pool, call)
    log.info(f"Submit(provider={pool.provider} model={body.model} request_id={response.request_id} status={response.status})")
    return serialize(pool.provider, body.model, key, response)


@app.post("/v1/submit_async")
def submit_async(body: SubmitBody) -> dict[str, Any]:
    if not body.webhook:
        raise GatewayError(400, "webhook is required for submit_async")
    pool = pool_for(body.provider)
    key, response = with_failover(
        pool,
        lambda adapter: adapter.submit_async(
            body.model, body.webhook, workflow=RAW_WORKFLOW, headers=body.headers, **body.input
        ),
    )
    log.info(f"SubmitAsync(provider={pool.provider} model={body.model} request_id={response.request_id})")
    return serialize(pool.provider, body.model, key, response)


@app.post("/v1/status")
def status(body: FollowUpBody) -> dict[str, Any]:
    pool = pool_for(body.provider)
    try:
        key, response = on_owning_key(pool, body.key_ref, lambda a: a.status(body.model, body.request_id))
    except HttpProviderError as error:
        # fal reports a failed job as COMPLETED on /status and returns the
        # error from the result fetch. Surface it as a failed job, not a
        # gateway error, so callers can branch on `status`.
        if error.status_code in _WRONG_KEY_STATUSES:
            raise
        return {
            "provider": pool.provider,
            "model": body.model,
            "request_id": body.request_id,
            "status": "failed",
            "result": None,
            "error": str(error),
            "provider_status": error.status_code,
            "raw_response": error.raw_response,
            "media_urls": [],
            "key_ref": body.key_ref,
        }
    return serialize(pool.provider, body.model, key, response)


@app.post("/v1/cancel")
def cancel(body: FollowUpBody) -> dict[str, Any]:
    pool = pool_for(body.provider)
    key, response = on_owning_key(pool, body.key_ref, lambda a: a.cancel(body.model, body.request_id))
    return serialize(pool.provider, body.model, key, response)


@app.post("/v1/upload")
async def upload(provider: str, request: Request) -> dict[str, Any]:
    """Re-host bytes on the provider CDN. Body is the raw file; Cloud Run caps it at 32 MB.

    Provider comes from the `?provider=` query parameter, since the body is raw bytes.
    Optional headers: `X-File-Name`, `X-Fal-Object-Lifecycle-Preference`.
    """
    pool = pool_for(provider)
    if not hasattr(PROVIDERS[pool.provider], "upload"):
        raise GatewayError(400, f"{pool.provider} does not support upload")
    data = await request.body()
    if not data:
        raise GatewayError(400, "empty upload body")
    content_type = request.headers.get("content-type", "application/octet-stream")
    file_name = request.headers.get("x-file-name")
    lifecycle = request.headers.get("x-fal-object-lifecycle-preference")
    extra = {"X-Fal-Object-Lifecycle-Preference": lifecycle} if lifecycle else None

    def call():
        return with_failover(
            pool, lambda adapter: adapter.upload(data, content_type, file_name, headers=extra)
        )

    key, url = await to_thread.run_sync(call)
    log.info(f"Upload(provider={pool.provider} bytes={len(data)} type={content_type})")
    return {"provider": pool.provider, "url": url, "key_ref": key_ref(key)}
