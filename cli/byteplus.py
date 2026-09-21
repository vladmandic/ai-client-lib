"""BytePlus ModelArk image and video adapter."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import mimetypes
import os
import time
from typing import Any

from urllib3.filepost import encode_multipart_formdata

from .core import (
    CapabilityError,
    ClientConfig,
    ProviderHttpClient,
    Response,
    validate_workflow_inputs,
)


class BytePlus(ProviderHttpClient):
    """Client for the documented ModelArk image and Seedance video APIs."""

    base_url = "https://ark.ap-southeast.bytepluses.com/api/v3"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
        base_url: str | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("BYTEPLUS_API_KEY")
        if key is None:
            raise ValueError("api_key or BYTEPLUS_API_KEY is required")
        super().__init__("byteplus", key, config)
        if base_url is not None:
            self.base_url = base_url.rstrip("/")

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
        selected_workflow = validate_workflow_inputs(model, image, video, workflow)
        if selected_workflow in {"text-to-image", "image-to-image", "edit"}:
            if video is not None:
                raise CapabilityError("BytePlus image generation does not accept video input")
            body = {"model": model, "prompt": prompt, **kwargs}
            if image is not None:
                body["image"] = self.prepare_media(image)
            status_code, response = self._request(
                "POST",
                "/images/generations",
                record.correlation_id,
                body,
            )
            self.resources.stats.update(
                record.correlation_id,
                request_id=record.correlation_id,
                status="completed",
                http_status=status_code,
                finish=True,
            )
            return self._normalize(response, record.correlation_id, "completed", record.correlation_id)
        if selected_workflow in {"text-to-video", "image-to-video", "video-to-video"}:
            return self._submit_video(model, prompt, image, video, selected_workflow, kwargs, record.correlation_id)
        raise CapabilityError(f"BytePlus workflow is unsupported: {selected_workflow}")

    def submit_async(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        raise CapabilityError("BytePlus tutorials do not document webhook submission")

    def status(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        _, response = self._request(
            "GET",
            f"/contents/generations/tasks/{request_id}",
            record.correlation_id,
        )
        status = self._status(response)
        self.resources.stats.update(
            record.correlation_id,
            request_id=request_id,
            status=status,
            finish=status in {"completed", "failed", "cancelled"},
        )
        return self._normalize(response, record.correlation_id, status, request_id)

    def cancel(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("cancel")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        _, response = self._request(
            "DELETE",
            f"/contents/generations/tasks/{request_id}",
            record.correlation_id,
        )
        self.resources.stats.update(record.correlation_id, status="cancelled", finish=True)
        return self._normalize(response, record.correlation_id, "cancelled", request_id)

    def upload_file(
        self,
        path: str | os.PathLike[str],
        *,
        purpose: str = "user_data",
        preprocess_configs: dict[str, Any] | None = None,
        expire_at: int | None = None,
    ) -> dict[str, Any]:
        """Upload a local asset through the ModelArk Files API."""
        file_name = os.path.basename(os.fspath(path))
        with open(path, "rb") as media_file:
            fields: dict[str, Any] = {
                "purpose": purpose,
                "file": (
                    file_name,
                    media_file.read(),
                    mimetypes.guess_type(file_name)[0] or "application/octet-stream",
                ),
            }
        self._add_file_options(fields, preprocess_configs, expire_at)
        return self._upload_multipart(fields)

    def upload_url(
        self,
        url: str,
        *,
        purpose: str = "user_data",
        preprocess_configs: dict[str, Any] | None = None,
        expire_at: int | None = None,
    ) -> dict[str, Any]:
        """Upload a public HTTP, HTTPS, or TOS asset through the Files API."""
        fields: dict[str, Any] = {"purpose": purpose, "url": url}
        self._add_file_options(fields, preprocess_configs, expire_at)
        return self._upload_multipart(fields)

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Retrieve File API metadata by file ID."""
        record = self.resources.stats.start("get_file")
        status_code, response = self._request("GET", f"/files/{file_id}", record.correlation_id)
        self.resources.stats.update(
            record.correlation_id,
            status="completed",
            http_status=status_code,
            finish=True,
        )
        return response

    def delete_file(self, file_id: str) -> dict[str, Any]:
        """Delete a File API asset by file ID."""
        record = self.resources.stats.start("delete_file")
        status_code, response = self._request("DELETE", f"/files/{file_id}", record.correlation_id)
        self.resources.stats.update(
            record.correlation_id,
            status="completed",
            http_status=status_code,
            finish=True,
        )
        return response

    @staticmethod
    def _add_file_options(
        fields: dict[str, Any],
        preprocess_configs: dict[str, Any] | None,
        expire_at: int | None,
    ) -> None:
        if expire_at is not None:
            fields["expire_at"] = str(expire_at)
        for category, options in (preprocess_configs or {}).items():
            if isinstance(options, dict):
                for name, value in options.items():
                    fields[f"preprocess_configs[{category}][{name}]"] = str(value)

    def _upload_multipart(self, fields: dict[str, Any]) -> dict[str, Any]:
        body, content_type = encode_multipart_formdata(fields)
        record = self.resources.stats.start("upload")
        correlation_id = record.correlation_id
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            response = self.resources.pool.request(
                "POST",
                f"{self.base_url}/files",
                body=body,
                headers={
                    "Authorization": f"Bearer {self._key_for_request()}",
                    "Content-Type": content_type,
                    "X-Correlation-ID": correlation_id,
                },
            )
            self.resources.stats.record_attempt(correlation_id, response.status)
            if response.status >= 400:
                raise RuntimeError(f"BytePlus file upload failed with HTTP {response.status}")
            result = self._decode(response)
            self.resources.stats.update(
                correlation_id,
                status="completed",
                http_status=response.status,
                finish=True,
            )
            return result
        finally:
            self.resources.stats.end_http()
            self.resources.release()

    def _submit_video(
        self,
        model: str,
        prompt: str,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        workflow: str,
        kwargs: dict[str, Any],
        correlation_id: str,
    ) -> Response:
        del workflow
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image is not None:
            image_url = self.prepare_media(image)
            content.append({"type": "image_url", "image_url": {"url": image_url}, "role": "first_frame"})
        if video is not None:
            video_url = str(video)
            if not video_url.startswith(("http://", "https://")):
                raise CapabilityError("BytePlus video inputs require public video URLs")
            content.append({"type": "video_url", "video_url": {"url": video_url}, "role": "reference_video"})
        body = {"model": model, "content": content, **kwargs}
        _, response = self._request(
            "POST",
            "/contents/generations/tasks",
            correlation_id,
            body,
        )
        request_id = self._task_id(response)
        self.resources.stats.update(correlation_id, request_id=request_id, status="queued")
        return self._poll(request_id, correlation_id)

    def _poll(self, request_id: str, correlation_id: str) -> Response:
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self.status(request_id)
            if response.status in {"completed", "failed", "cancelled"}:
                return response
            time.sleep(self.config.poll_interval)
        self.resources.stats.update(correlation_id, error="polling timeout")
        raise TimeoutError(f"BytePlus task {request_id} polling timed out")

    def _request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        headers = {
            "Authorization": f"Bearer {self._key_for_request()}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
        }
        return self.request_json(
            method,
            f"{self.base_url}{path}",
            body=body,
            headers=headers,
            correlation_id=correlation_id,
            operation=method,
        )

    @staticmethod
    def _task_id(response: Any) -> str:
        if not isinstance(response, dict) or not response.get("id"):
            raise RuntimeError("BytePlus response did not include a task id")
        return str(response["id"])

    @staticmethod
    def _status(response: Any) -> str:
        value = str(response.get("status", "")).lower() if isinstance(response, dict) else ""
        return {
            "queued": "queued",
            "running": "processing",
            "succeeded": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
            "expired": "failed",
        }.get(value, "processing")

    @staticmethod
    def _normalize(
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str,
    ) -> Response:
        error = response.get("error") if isinstance(response, dict) else None
        result = None
        if status == "completed" and isinstance(response, dict):
            result = response.get("content", response.get("data"))
        return Response(
            request_id=request_id,
            status=status,
            result=result,
            error=str(error) if error else None,
            raw_response=response,
            correlation_id=correlation_id,
        )
