"""fal.ai queue adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import os
import time
from typing import Any

from .core import (
    ClientConfig,
    ProviderHttpClient,
    Response,
    extract_media_urls,
    validate_workflow_inputs,
)


class Fal(ProviderHttpClient):
    """Client for fal.ai queue-backed model APIs."""

    base_url = "https://queue.fal.run"

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
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit")
        validate_workflow_inputs(model, image, video, workflow)
        image = self.prepare_media(image)
        video = self.prepare_media(video)
        body = self._payload(model, prompt, image, video, kwargs)
        response = self._queue_submit(model, body, record.correlation_id)
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
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit_async")
        validate_workflow_inputs(model, image, video, workflow)
        image = self.prepare_media(image)
        video = self.prepare_media(video)
        body = self._payload(model, prompt, image, video, kwargs)
        response = self._queue_submit(model, body, record.correlation_id, webhook)
        request_id = self._request_id(response)
        self.resources.stats.update(
            record.correlation_id,
            request_id=request_id,
            status="queued",
        )
        return self._normalize(response, record.correlation_id, "queued", request_id, raw_request=body)

    def status(self, model: str, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._request(
            "GET",
            f"{self.base_url}/{model}/requests/{request_id}/status",
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
                f"{self.base_url}/{model}/requests/{request_id}",
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
            f"{self.base_url}/{model}/requests/{request_id}/cancel",
            record.correlation_id,
            "cancel",
        )
        normalized_status = self._status(response)
        if normalized_status not in {"cancelled", "failed", "completed"}:
            normalized_status = "cancelled"
        self.resources.stats.update(record.correlation_id, status=normalized_status, finish=True)
        return self._normalize(response, record.correlation_id, normalized_status, request_id)

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
            status_url = f"{self.base_url}/{model}/requests/{request_id}/status"
        if response_url is None:
            response_url = f"{self.base_url}/{model}/requests/{request_id}"
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
    ) -> Any:
        url = f"{self.base_url}/{model}"
        if webhook is not None:
            url = f"{url}?fal_webhook={webhook}"
        return self._request("POST", url, correlation_id, "submit", body)

    def _request(
        self,
        method: str,
        url: str,
        correlation_id: str,
        operation: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
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
