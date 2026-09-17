"""PixVerse video generation adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import os
import time
from typing import Any
from uuid import uuid4

from .core import (
    CapabilityError,
    ClientConfig,
    ProviderHttpClient,
    Response,
    validate_workflow_inputs,
)


class Pixverse(ProviderHttpClient):
    """Client for PixVerse text-to-video and image-to-video APIs."""

    base_url = "https://app-api.pixverse.ai/openapi/v2"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("PIXVERSE_API_KEY")
        if key is None:
            raise ValueError("api_key or PIXVERSE_API_KEY is required")
        super().__init__("pixverse", key, config)

    def submit(
        self,
        model: str,
        prompt: str,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit")
        workflow = validate_workflow_inputs(model, image, video, workflow)
        if workflow not in {"text-to-video", "image-to-video"}:
            raise CapabilityError("PixVerse documents text-to-video and image-to-video workflows")
        trace_id = str(uuid4())
        body = self._payload(model, workflow, prompt, image, video, kwargs)
        response = self._request(workflow, "POST", body, trace_id, record.correlation_id)
        request_id = self._video_id(response)
        self.resources.stats.update(record.correlation_id, request_id=request_id, status="queued")
        return self._poll(request_id, workflow, trace_id, record.correlation_id)

    def submit_async(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        raise CapabilityError("PixVerse callback/webhook submission is not documented")

    def status(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        trace_id = record.correlation_id
        response = self._status_request(request_id, trace_id, record.correlation_id)
        status = self._status(response)
        self.resources.stats.update(record.correlation_id, status=status, finish=status in {"completed", "failed"})
        return self._normalize(response, record.correlation_id, status, request_id)

    def cancel(self, request_id: str) -> Response:
        del request_id
        raise CapabilityError("PixVerse cancellation is not documented")

    def _poll(
        self,
        request_id: str,
        workflow: str,
        trace_id: str,
        correlation_id: str,
    ) -> Response:
        del workflow
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self._status_request(request_id, trace_id, correlation_id)
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status in {"completed", "failed"}:
                self.resources.stats.update(correlation_id, status=status, finish=True)
                return self._normalize(response, correlation_id, status, request_id)
            time.sleep(self.config.poll_interval)
        self.resources.stats.update(correlation_id, error="polling timeout")
        raise TimeoutError(f"PixVerse video {request_id} polling timed out")

    def _request(
        self,
        workflow: str,
        method: str,
        body: dict[str, Any],
        trace_id: str,
        correlation_id: str,
    ) -> Any:
        endpoint = "text/generate" if workflow == "text-to-video" else "img/generate"
        headers = self._headers(trace_id)
        _, response = self.request_json(
            method,
            f"{self.base_url}/video/{endpoint}",
            body=body,
            headers=headers,
            correlation_id=correlation_id,
            operation="submit",
        )
        return response

    def _status_request(self, request_id: str, trace_id: str, correlation_id: str) -> Any:
        headers = self._headers(trace_id)
        _, response = self.request_json(
            "GET",
            f"{self.base_url}/video/result/{request_id}",
            body=None,
            headers=headers,
            correlation_id=correlation_id,
            operation="status",
        )
        return response

    def _headers(self, trace_id: str) -> dict[str, str]:
        return {
            "API-KEY": self._key_for_request(),
            "Ai-trace-id": trace_id,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _payload(
        model: str,
        workflow: str,
        prompt: str,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        if video is not None:
            raise CapabilityError("PixVerse video-to-video is not documented by these endpoints")
        payload = {"model": model.rsplit("/", 1)[0], "prompt": prompt, **kwargs}
        if workflow == "image-to-video":
            if image is None:
                raise CapabilityError("PixVerse image-to-video requires an image")
            if "img_id" not in payload:
                raise CapabilityError("PixVerse image-to-video requires an uploaded img_id")
        return payload

    @staticmethod
    def _video_id(response: Any) -> str:
        try:
            return str(response["Resp"]["video_id"])
        except (KeyError, TypeError) as error:
            raise RuntimeError("PixVerse response did not include Resp.video_id") from error

    @staticmethod
    def _status(response: Any) -> str:
        try:
            value = response["Resp"]["status"]
        except (KeyError, TypeError):
            return "failed"
        return {1: "completed", 5: "processing", 7: "failed", 8: "failed"}.get(value, "processing")

    @staticmethod
    def _normalize(
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str,
    ) -> Response:
        error = response.get("ErrMsg") if isinstance(response, dict) else None
        result = response.get("Resp") if status == "completed" and isinstance(response, dict) else None
        return Response(
            request_id=request_id,
            status=status,
            result=result,
            error=str(error) if error and status == "failed" else None,
            raw_response=response,
            correlation_id=correlation_id,
        )
