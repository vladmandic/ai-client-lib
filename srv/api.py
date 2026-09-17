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
    async def post_webhook(payload: dict, request: Request):
        # saved_media = _save_media(app, provider, str(request_id or "unknown"), payload)
        headers = dict(request.headers)
        event = {
            "received_at": datetime.now(UTC).isoformat(),
            "headers": headers,
            "payload": payload,
        }
        with lock:
            getattr(app.state, WEBHOOK_EVENTS).append(event)
        log.info(f"Webhook(headers={headers} payload={payload})")
        return { "accepted": True }
