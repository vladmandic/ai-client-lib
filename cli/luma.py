"""Luma Agents image and video generation adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

from .core import (
    CapabilityError,
    ClientConfig,
    ProviderError,
    ProviderHttpClient,
    Response,
    extract_media_urls,
    validate_workflow_inputs,
)


class Luma(ProviderHttpClient):
    """Client for Luma Agents generations."""

    base_url = "https://agents.lumalabs.ai/v1"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("LUMA_API_KEY")
        if key is None:
            raise ValueError("api_key or LUMA_API_KEY is required")
        super().__init__("luma", key, config)

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
        selected_workflow = validate_workflow_inputs(model, image, video, workflow)
        if selected_workflow == "video-to-video":
            raise CapabilityError("Luma video-to-video is not documented")
        body = self._payload(
            model,
            prompt,
            self.prepare_media(image),
            selected_workflow,
            kwargs,
        )
        response = self._request("POST", "/generations", record.correlation_id, body, "submit")
        request_id = self._request_id(response)
        self.resources.stats.update(record.correlation_id, request_id=request_id, status="queued")
        return self._poll(request_id, record.correlation_id, raw_request=body)

    def submit_async(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        raise CapabilityError("Luma webhook submission is not documented")

    def status(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._request(
            "GET",
            f"/generations/{quote(request_id, safe='')}",
            record.correlation_id,
            operation="status",
        )
        status = self._status(response)
        self.resources.stats.update(
            record.correlation_id,
            status=status,
            finish=status in {"completed", "failed"},
        )
        return self._normalize(response, record.correlation_id, status, request_id)

    def cancel(self, request_id: str) -> Response:
        del request_id
        raise CapabilityError("Luma cancellation is not documented")

    def _poll(
        self,
        request_id: str,
        correlation_id: str,
        raw_request: Any = None,
    ) -> Response:
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self._request(
                "GET",
                f"/generations/{quote(request_id, safe='')}",
                correlation_id,
                operation="status",
            )
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status in {"completed", "failed"}:
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
        raise TimeoutError(f"Luma generation {request_id} polling timed out")

    def _request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        body: dict[str, Any] | None = None,
        operation: str = "submit",
    ) -> Any:
        _, response = self.request_json(
            method,
            f"{self.base_url}{path}",
            body=body,
            headers={
                "Authorization": f"Bearer {self._key_for_request()}",
                "Content-Type": "application/json",
                "X-Correlation-ID": correlation_id,
            },
            correlation_id=correlation_id,
            operation=operation,
        )
        return response

    @classmethod
    def _payload(
        cls,
        model: str,
        prompt: str | None,
        image: str | None,
        workflow: str,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        if not prompt:
            raise ValueError("prompt is required")

        if workflow == "text-to-image":
            generation_type = "image"
        elif workflow in {"image-to-image", "edit"}:
            generation_type = "image_edit"
        elif workflow in {"text-to-video", "image-to-video"}:
            generation_type = "video"
        else:
            raise CapabilityError(f"Luma does not support the {workflow} workflow")

        payload = dict(kwargs)
        payload.update({"model": model, "type": generation_type, "prompt": prompt})

        if workflow in {"image-to-image", "edit"}:
            payload["source"] = cls._image_ref(image)
        elif workflow == "image-to-video":
            video_options = payload.get("video", {})
            if not isinstance(video_options, dict):
                raise TypeError("video options must be a dictionary")
            payload["video"] = {**video_options, "start_frame": cls._image_ref(image)}
        elif workflow == "text-to-video":
            video_options = payload.get("video", {})
            if not isinstance(video_options, dict):
                raise TypeError("video options must be a dictionary")
            payload["video"] = video_options

        return payload

    @staticmethod
    def _image_ref(value: str | None) -> dict[str, str]:
        if value is None:
            raise CapabilityError("Luma image workflows require an image")
        if value.startswith("data:"):
            header, separator, data = value.partition(",")
            if not separator or ";base64" not in header:
                raise ValueError("Luma image data URI must contain base64-encoded data")
            return {"data": data, "media_type": header[5:].split(";", maxsplit=1)[0]}
        return {"url": value}

    @staticmethod
    def _request_id(response: Any) -> str:
        if isinstance(response, dict) and response.get("id"):
            return str(response["id"])
        raise ProviderError("Luma response did not include a generation id")

    @staticmethod
    def _status(response: Any) -> str:
        state = str(response.get("state", "")).lower() if isinstance(response, dict) else ""
        if state in {"queued", "processing", "completed", "failed"}:
            return state
        return "failed" if isinstance(response, dict) and response.get("failure_reason") else "processing"

    @classmethod
    def _normalize(
        cls,
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str | None,
        raw_request: Any = None,
    ) -> Response:
        error = None
        if isinstance(response, dict):
            error = response.get("failure_reason") or response.get("detail")
        result = response if status == "completed" else None
        urls = extract_media_urls(response.get("output")) if status == "completed" and isinstance(response, dict) else []
        media_url = urls[0] if len(urls) == 1 else urls or None
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
