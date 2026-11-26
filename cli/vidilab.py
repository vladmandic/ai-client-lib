"""VidLab image and video generation adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import mimetypes
import os
import time
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import urllib3

from .core import (
    CapabilityError,
    ClientConfig,
    HttpProviderError,
    ProviderError,
    ProviderHttpClient,
    Response,
    extract_media_urls,
    validate_workflow_inputs,
)


class Vidilab(ProviderHttpClient):
    """Client for VidLab's unified generations API."""

    base_url = "https://vidlab.ai/v1"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("VIDILAB_API_KEY")
        if key is None:
            raise ValueError("api_key or VIDILAB_API_KEY is required")
        super().__init__("vidilab", key, config)

    def submit(
        self,
        model: str,
        prompt: str | None = None,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit")
        api_key = self._key_for_request()
        body = self._payload(
            model,
            prompt,
            image,
            video,
            workflow,
            kwargs,
            record.correlation_id,
            api_key,
        )
        key = idempotency_key or str(uuid4())
        _, response = self._request(
            "POST",
            "/generations",
            record.correlation_id,
            operation="submit",
            body=body,
            api_key=api_key,
            headers=headers,
            idempotency_key=key,
        )
        generation_id = self._generation_id(response)
        status = self._status(response)
        self.resources.stats.update(record.correlation_id, request_id=generation_id, status=status)
        return self._poll(
            generation_id,
            record.correlation_id,
            api_key,
            raw_request=body,
            headers=headers,
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
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> Response:
        if not webhook:
            raise ValueError("webhook is required")
        record = self.resources.stats.start("submit_async")
        api_key = self._key_for_request()
        body = self._payload(
            model,
            prompt,
            image,
            video,
            workflow,
            kwargs,
            record.correlation_id,
            api_key,
        )
        body["webhook_url"] = webhook
        key = idempotency_key or str(uuid4())
        _, response = self._request(
            "POST",
            "/generations",
            record.correlation_id,
            operation="submit_async",
            body=body,
            api_key=api_key,
            headers=headers,
            idempotency_key=key,
        )
        generation_id = self._generation_id(response)
        status = self._status(response)
        self.resources.stats.update(
            record.correlation_id,
            request_id=generation_id,
            status=status,
            finish=status in {"completed", "failed"},
        )
        return self._normalize(response, record.correlation_id, status, generation_id, body)

    def status(self, request_id: str, *, wait: int = 0) -> Response:
        if not 0 <= wait <= 60:
            raise ValueError("wait must be between 0 and 60 seconds")
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._get_generation(request_id, record.correlation_id, wait, self._key_for_request())
        status = self._status(response)
        self.resources.stats.update(
            record.correlation_id,
            status=status,
            finish=status in {"completed", "failed"},
        )
        return self._normalize(response, record.correlation_id, status, request_id)

    def cancel(self, request_id: str) -> Response:
        del request_id
        raise CapabilityError("VidLab generation cancellation is not documented")

    def _poll(
        self,
        request_id: str,
        correlation_id: str,
        api_key: str,
        *,
        raw_request: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        deadline = time.monotonic() + self.config.poll_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.resources.stats.update(correlation_id, error="polling timeout")
                raise TimeoutError(f"VidLab generation {request_id} polling timed out")
            wait = min(60, int(remaining))
            response = self._get_generation(request_id, correlation_id, wait, api_key, headers)
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status in {"completed", "failed"}:
                self.resources.stats.update(correlation_id, status=status, finish=True)
                return self._normalize(response, correlation_id, status, request_id, raw_request)
            if self.config.poll_interval > 0:
                time.sleep(min(self.config.poll_interval, max(0, deadline - time.monotonic())))

    def _get_generation(
        self,
        request_id: str,
        correlation_id: str,
        wait: int,
        api_key: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        query = f"?wait={wait}" if wait else ""
        _, response = self._request(
            "GET",
            f"/generations/{quote(request_id, safe='')}{query}",
            correlation_id,
            operation="status",
            api_key=api_key,
            headers=headers,
        )
        return response

    def _request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        *,
        operation: str,
        body: dict[str, Any] | None = None,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[int, Any]:
        request_headers = dict(headers or {})
        request_headers.update(
            {
                "Authorization": f"Bearer {api_key or self._key_for_request()}",
                "Content-Type": "application/json",
                "X-Correlation-ID": correlation_id,
            }
        )
        if idempotency_key is not None:
            request_headers["Idempotency-Key"] = idempotency_key
        return self.request_json(
            method,
            f"{self.base_url}{path}",
            body=body,
            headers=request_headers,
            correlation_id=correlation_id,
            operation=operation,
        )

    def _payload(
        self,
        model: str,
        prompt: str | None,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        workflow: str | None,
        kwargs: dict[str, Any],
        correlation_id: str,
        api_key: str,
    ) -> dict[str, Any]:
        selected_workflow = validate_workflow_inputs(model, image, video, workflow)
        if selected_workflow == "video-to-video":
            raise CapabilityError("VidLab video-to-video is not documented for these models")
        if not prompt:
            raise ValueError("prompt is required")
        input_data = dict(kwargs)
        if "max_cost_usd" in input_data:
            max_cost = input_data.pop("max_cost_usd")
        else:
            max_cost = None
        if "max_wait_s" in input_data:
            max_wait = input_data.pop("max_wait_s")
        else:
            max_wait = None
        if "images" in input_data and image is not None:
            raise ValueError("pass image or images, not both")
        input_data["prompt"] = prompt
        if image is not None:
            input_data["images"] = [self._prepare_image(image, correlation_id, api_key)]
        if video is not None:
            raise CapabilityError("VidLab video input is not documented for these models")
        body: dict[str, Any] = {"model": model, "input": input_data}
        if max_cost is not None:
            body["max_cost_usd"] = max_cost
        if max_wait is not None:
            body["max_wait_s"] = max_wait
        return body

    def _prepare_image(
        self,
        image: str | os.PathLike[str],
        correlation_id: str,
        api_key: str,
    ) -> str:
        value = os.fspath(image)
        if value.startswith(("http://", "https://", "data:")):
            return value
        file_name = os.path.basename(value)
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        with open(value, "rb") as media_file:
            data = media_file.read()
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            self.resources.rate_limit(self.config.requests_per_second)
            response = self.resources.pool.request(
                "POST",
                f"{self.base_url}/uploads",
                body=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": content_type,
                    "X-File-Name": file_name,
                    "X-Correlation-ID": correlation_id,
                },
                preload_content=True,
            )
            self.resources.stats.record_attempt(correlation_id, response.status)
        except urllib3.exceptions.HTTPError as error:
            raise ProviderError("VidLab upload request failed") from error
        finally:
            self.resources.stats.end_http()
            self.resources.release()
        result = self._decode(response)
        if response.status >= 400:
            raise HttpProviderError(response.status, self._error_message(result), raw_response=result)
        try:
            return str(result["data"]["url"])
        except (KeyError, TypeError) as error:
            raise ProviderError("VidLab upload response did not include data.url") from error

    @staticmethod
    def _generation_id(response: Any) -> str:
        try:
            return str(response["data"]["id"])
        except (KeyError, TypeError) as error:
            raise ProviderError("VidLab response did not include a generation id") from error

    @staticmethod
    def _generation(response: Any) -> dict[str, Any]:
        if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
            return {}
        return response["data"]

    @classmethod
    def _status(cls, response: Any) -> str:
        value = str(cls._generation(response).get("status", "")).lower()
        return {
            "queued": "queued",
            "running": "processing",
            "succeeded": "completed",
            "failed": "failed",
        }.get(value, "failed")

    @classmethod
    def _normalize(
        cls,
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str,
        raw_request: Any = None,
    ) -> Response:
        generation = cls._generation(response)
        error = generation.get("error")
        if isinstance(error, dict):
            error = error.get("message") or error.get("code") or str(error)
        result = generation if status == "completed" else None
        urls = extract_media_urls(generation.get("outputs")) if status == "completed" else []
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
