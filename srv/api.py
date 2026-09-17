import mimetypes
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse
import urllib3
from fastapi import FastAPI, Header, Request, status
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
from uvicorn import Server

from .logger import log

lock = Lock()
WEBHOOK_EVENTS = "webhook_events"
WEBHOOK_POOL = "webhook_pool"
WEBHOOK_MEDIA_DIR = "webhook_media_dir"


def _media_urls(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "resultUrls" and isinstance(child, list):
                yield from (item for item in child if isinstance(item, str))
            elif key.endswith("url") and isinstance(child, str):
                yield child
            else:
                yield from _media_urls(child)
    elif isinstance(value, list):
        for child in value:
            yield from _media_urls(child)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "webhook"


def _save_media(app, provider: str, request_id: str, payload: dict) -> list[str]:
    urls = list(dict.fromkeys(_media_urls(payload)))
    if not urls:
        return []
    media_dir = Path(getattr(app.state, WEBHOOK_MEDIA_DIR))
    media_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for index, url in enumerate(urls):
        try:
            response = getattr(app.state, WEBHOOK_POOL).request("GET", url, preload_content=True)
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            suffix = Path(urlparse(url).path).suffix
            if not suffix:
                suffix = mimetypes.guess_extension(response.headers.get("Content-Type", "")) or ".bin"
            stem = f"{_safe_filename(provider)}-{_safe_filename(request_id)}"
            if len(urls) > 1:
                stem = f"{stem}-{index + 1}"
            destination = media_dir / f"{stem}{suffix}"
            destination.write_bytes(response.data)
            saved.append(str(destination))
        except Exception as error:  # pylint: disable=broad-exception-caught
            log.warning("WebhookMedia(url=%s saved=False error=%s)", url, error)
    return saved


def mount(server: Server, prefix: str = ''):
    app: FastAPI = server.app
    if not hasattr(app.state, WEBHOOK_EVENTS):
        setattr(app.state, WEBHOOK_EVENTS, [])
    if not hasattr(app.state, WEBHOOK_POOL):
        setattr(app.state, WEBHOOK_POOL, urllib3.PoolManager())
    if not hasattr(app.state, WEBHOOK_MEDIA_DIR):
        setattr(app.state, WEBHOOK_MEDIA_DIR, os.environ.get("WEBHOOK_MEDIA_DIR", "media"))

    @app.get("/", response_description="root", response_model=str)
    async def get_root(request: Request):
        log.debug(f'GET(endpoint=/root request={request})')
        return "echonos.ai private server"

    @app.get(f"{prefix}/ping", response_description="server ping", response_model=str)
    async def get_ping(message: str = Header(None)):
        log.debug(f'GET(endpoint={prefix}/ping) msg="{message}"')
        return f"pong: {message}"


    @app.get(f"{prefix}/samples", response_description="list sample media", response_model=list[str])
    async def list_samples():
        log.debug(f'GET(endpoint={prefix}/samples)')
        samples_dir = 'samples'
        if not os.path.exists(samples_dir) or not os.path.isdir(samples_dir):
            return []
        return [f for f in os.listdir(samples_dir) if os.path.isfile(os.path.join(samples_dir, f))]

    @app.get(f"{prefix}/samples/" + "{filename}", response_description="get sample media", response_class=FileResponse)
    async def get_samples(filename: str):
        log.debug(f'GET(endpoint={prefix}/samples/ filename={filename})')
        safe = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).strip()
        safe = os.path.join('samples', safe)
        print('HERE', safe)
        if not os.path.exists(safe) or not os.path.isfile(safe):
            return HTTPException(status_code=404, detail="File not found")
        return FileResponse(safe)

    @app.post(
        f"{prefix}/webhook",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=dict,
        response_description="webhook accepted",
    )
    async def post_webhook(
        payload: dict,
        provider: str | None = Header(default=None, alias="X-Provider"),
    ):
        request_id = payload.get("request_id") or payload.get("taskId") or payload.get("id")
        provider = provider or payload.get("provider") or "unknown"
        saved_media = _save_media(app, provider, str(request_id or "unknown"), payload)
        event = {
            "received_at": datetime.now(UTC).isoformat(),
            "provider": provider,
            "request_id": str(request_id) if request_id is not None else None,
            "status": payload.get("status") or payload.get("state"),
            "payload": payload,
            "saved_media": saved_media,
        }
        with lock:
            getattr(app.state, WEBHOOK_EVENTS).append(event)
        log.info(
            "Webhook(provider=%s request_id=%s status=%s accepted=True)",
            provider,
            event["request_id"],
            event["status"],
        )
        return {
            "accepted": True,
            "request_id": event["request_id"],
            "saved_media": saved_media,
        }
