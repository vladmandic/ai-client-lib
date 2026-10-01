"""fal.ai queue adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import quote

import urllib3

from .core import (
    ClientConfig,
    HttpProviderError,
    ProviderError,
    ProviderHttpClient,
    Response,
    extract_media_urls,
    validate_workflow_inputs,
)


class Fal(ProviderHttpClient):
    """Client for fal.ai queue-backed model APIs."""

    base_url = "https://queue.fal.run"
    rest_url = "https://rest.fal.ai"
    cdn_url = "https://v3.fal.media"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("FAL_API_KEY")
        if key is None:
            raise ValueError("api_key or FAL_API_KEY is required")
        super().__init__("fal", key, config)

    def submit(
        self,
        model: str,
        prompt: str | None = None,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit")
        validate_workflow_inputs(model, image, video, workflow)
        image = self.prepare_media(image)
        video = self.prepare_media(video)
        body = self._payload(model, prompt, image, video, kwargs)
        response = self._queue_submit(model, body, record.correlation_id, headers=headers)
        request_id = self._request_id(response)
        self.resources.stats.update(
            record.correlation_id,
            request_id=request_id,
            status="queued",
        )
        status_url = response.get("status_url") if isinstance(response, dict) else None
        response_url = response.get("response_url") if isinstance(response, dict) else None
        return self._poll(
            model,
            request_id,
            record.correlation_id,
            status_url=status_url,
            response_url=response_url,
            raw_request=body,
        )

    def submit_async(
        self,
        model: str,
        webhook: str,
        prompt: str | None = None,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit_async")
        validate_workflow_inputs(model, image, video, workflow)
        image = self.prepare_media(image)
        video = self.prepare_media(video)
        body = self._payload(model, prompt, image, video, kwargs)
        response = self._queue_submit(model, body, record.correlation_id, webhook, headers=headers)
        request_id = self._request_id(response)
        self.resources.stats.update(
            record.correlation_id,
            request_id=request_id,
            status="queued",
        )
        return self._normalize(response, record.correlation_id, "queued", request_id, raw_request=body)

    def _queue_root(self, model: str) -> str:
        """Queue URL for follow-ups (status/result/cancel) on a request.

        fal submits to the full endpoint (`fal-ai/flux/schnell`) but addresses
        the queued request by app only (`fal-ai/flux`); keeping the subpath
        returns 405. Same rule fal_client applies.
        """
        app = "/".join(model.strip("/").split("/")[:2])
        return f"{self.base_url}/{app}"

    def status(self, model: str, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._request(
            "GET",
            f"{self._queue_root(model)}/requests/{request_id}/status",
            record.correlation_id,
            "status",
        )
        normalized_status = self._status(response)
        self.resources.stats.update(
            record.correlation_id,
            status=normalized_status,
            finish=normalized_status in {"completed", "failed", "cancelled"},
        )
        if normalized_status == "completed":
            response = self._request(
                "GET",
                f"{self._queue_root(model)}/requests/{request_id}",
                record.correlation_id,
                "result",
            )
        return self._normalize(response, record.correlation_id, normalized_status, request_id)

    def cancel(self, model: str, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("cancel")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._request(
            "PUT",
            f"{self._queue_root(model)}/requests/{request_id}/cancel",
            record.correlation_id,
            "cancel",
        )
        normalized_status = self._status(response)
        if normalized_status not in {"cancelled", "failed", "completed"}:
            normalized_status = "cancelled"
        self.resources.stats.update(record.correlation_id, status=normalized_status, finish=True)
        return self._normalize(response, record.correlation_id, normalized_status, request_id)

    def upload(
        self,
        data: bytes,
        content_type: str,
        file_name: str | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Upload bytes to the fal CDN (v3, single part) and return the access URL.

        Mirrors fal_client's `fal_v3` repository: exchange the API key for a
        short-lived CDN token, then POST the raw bytes. Single-part only; the
        SDK switches to multipart above 100 MB.
        """
        key = self._key_for_request()
        token = self._raw_request(
            "POST",
            f"{self.rest_url}/storage/auth/token?storage_type=fal-cdn-v3",
            json.dumps({}).encode(),
            {"Authorization": f"Key {key}", "Content-Type": "application/json", "Accept": "application/json"},
        )
        upload_headers = {**(headers or {}), "Content-Type": content_type}
        if file_name:
            upload_headers["X-Fal-File-Name"] = file_name
        upload_headers["Authorization"] = f"{token['token_type']} {token['token']}"
        result = self._raw_request("POST", f"{self.cdn_url}/files/upload", data, upload_headers)
        return str(result["access_url"])

    def _raw_request(self, method: str, url: str, body: bytes, headers: dict[str, str]) -> Any:
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            response = self.resources.pool.request(method, url, body=body, headers=headers, preload_content=True)
        except urllib3.exceptions.HTTPError as error:
            raise ProviderError("fal upload request failed") from error
        finally:
            self.resources.stats.end_http()
            self.resources.release()
        data = self._decode(response)
        if response.status >= 400:
            raise HttpProviderError(response.status, self._error_message(data), raw_response=data)
        return data

    def _poll(
        self,
        model: str,
        request_id: str,
        correlation_id: str,
        status_url: str | None = None,
        response_url: str | None = None,
        raw_request: Any = None,
    ) -> Response:
        if status_url is None:
            status_url = f"{self._queue_root(model)}/requests/{request_id}/status"
        if response_url is None:
            response_url = f"{self._queue_root(model)}/requests/{request_id}"
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self._request(
                "GET",
                status_url,
                correlation_id,
                "status",
            )
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status == "completed":
                result = self._request(
                    "GET",
                    response_url,
                    correlation_id,
                    "result",
                )
                self.resources.stats.update(correlation_id, status="completed", finish=True)
                return self._normalize(
                    result,
                    correlation_id,
                    "completed",
                    request_id,
                    raw_request=raw_request,
                )
            if status in {"failed", "cancelled"}:
                self.resources.stats.update(correlation_id, status=status, finish=True)
                return self._normalize(
                    response,
                    correlation_id,
                    status,
                    request_id,
                    raw_request=raw_request,
                )
            time.sleep(self.config.poll_interval)
        self.resources.stats.update(correlation_id, error="polling timeout")
        raise TimeoutError(f"fal request {request_id} polling timed out")

    def _queue_submit(
        self,
        model: str,
        body: dict[str, Any],
        correlation_id: str,
        webhook: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{model}"
        if webhook is not None:
            url = f"{url}?fal_webhook={quote(webhook, safe='')}"
        return self._request("POST", url, correlation_id, "submit", body, headers)

    def _request(
        self,
        method: str,
        url: str,
        correlation_id: str,
        operation: str,
        body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        # Extra headers first so they can never override authentication.
        headers = {
            **(extra_headers or {}),
            "Authorization": f"Key {self._key_for_request()}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
        }
        _, response = self.request_json(
            method,
            url,
            body=body,
            headers=headers,
            correlation_id=correlation_id,
            operation=operation,
        )
        return response

    @classmethod
    def _payload(
        cls,
        model: str,
        prompt: str | None,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(kwargs)
        if prompt is not None:
            payload["prompt"] = prompt
        if image is not None:
            image_str = str(image)
            if "banana" in model.lower():
                payload["image_urls"] = [image_str]
            else:
                payload["image_url"] = image_str
        if video is not None:
            payload["video_url"] = str(video)
        return payload

    @staticmethod
    def _request_id(response: Any) -> str:
        if not isinstance(response, dict) or not response.get("request_id"):
            raise ProviderStatsError("fal response did not include request_id")
        return str(response["request_id"])

    @staticmethod
    def _status(response: Any) -> str:
        value = str(response.get("status", "")).upper() if isinstance(response, dict) else ""
        return {
            "IN_QUEUE": "queued",
            "IN_PROGRESS": "processing",
            "COMPLETED": "completed",
            "CANCELLATION_REQUESTED": "cancelled",
            "CANCELLED": "cancelled",
            "FAILED": "failed",
            "ERROR": "failed",
        }.get(value, "failed" if isinstance(response, dict) and response.get("error") else "processing")

    @classmethod
    def _extract_media_url(cls, response: Any) -> str | list[str] | None:
        urls: list[str] = []
        if isinstance(response, dict):
            if "images" in response:
                urls.extend(extract_media_urls(response["images"]))
            if "video" in response:
                urls.extend(extract_media_urls(response["video"]))
            if "image" in response:
                urls.extend(extract_media_urls(response["image"]))
        if not urls and response is not None:
            urls = extract_media_urls(response)
        if not urls:
            return None
        return urls[0] if len(urls) == 1 else urls

    @classmethod
    def _normalize(
        cls,
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str | None,
        raw_request: Any = None,
    ) -> Response:
        error = response.get("error") if isinstance(response, dict) else None
        result = response if status == "completed" else None
        media_url = cls._extract_media_url(result) if status == "completed" else None
        return Response(
            request_id=request_id,
            status=status,
            result=result,
            error=str(error) if error else None,
            raw_response=response,
            correlation_id=correlation_id,
            raw_request=raw_request,
            media_url=media_url,
        )


class ProviderStatsError(RuntimeError):
    """Raised when a provider response lacks required tracking data."""
