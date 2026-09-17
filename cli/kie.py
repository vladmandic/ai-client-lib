"""KIE Market API adapter for verified example models."""

# Provider adapters intentionally keep parallel lifecycle methods.
# pylint: disable=duplicate-code

from __future__ import annotations

import json
import mimetypes
import os
import time
from typing import Any
from urllib.parse import urlencode

from urllib3.filepost import encode_multipart_formdata

from .core import (
    CapabilityError,
    ClientConfig,
    HttpProviderError,
    ProviderHttpClient,
    Response,
    validate_workflow_inputs,
)


class Kie(ProviderHttpClient):
    """Client for the verified KIE Seedream and Kling Market models."""

    base_url = "https://api.kie.ai"
    upload_url = "https://kieai.redpandaai.co/api/file-stream-upload"

    def __init__(
        self,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("KIE_API_KEY")
        if key is None:
            raise ValueError("api_key or KIE_API_KEY is required")
        super().__init__("kie", key, config)

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
        api_key = self._key_for_request()
        image, video = self._prepare_media(image, video, record.correlation_id, api_key)
        body = self._body(model, prompt, image, video, workflow, kwargs)
        response = self._request("POST", "/api/v1/jobs/createTask", record.correlation_id, body, api_key)
        task_id = self._task_id(response)
        if task_id is None:
            error_msg = self._extract_error(response)
            self.resources.stats.update(
                record.correlation_id,
                status="failed",
                error=error_msg,
                finish=True,
            )
            return self._normalize(
                response,
                record.correlation_id,
                "failed",
                "",
                raw_request=body,
            )
        self.resources.stats.update(record.correlation_id, request_id=task_id, status="queued")
        return self._poll(task_id, record.correlation_id, api_key, raw_request=body)

    def submit_async(
        self,
        model: str,
        webhook: str,
        prompt: str,
        image: str | os.PathLike[str] | None = None,
        video: str | os.PathLike[str] | None = None,
        workflow: str | None = None,
        **kwargs: Any,
    ) -> Response:
        record = self.resources.stats.start("submit_async")
        api_key = self._key_for_request()
        image, video = self._prepare_media(image, video, record.correlation_id, api_key)
        body = self._body(model, prompt, image, video, workflow, kwargs)
        body["callBackUrl"] = webhook
        response = self._request("POST", "/api/v1/jobs/createTask", record.correlation_id, body, api_key)
        task_id = self._task_id(response)
        if task_id is None:
            error_msg = self._extract_error(response)
            self.resources.stats.update(
                record.correlation_id,
                status="failed",
                error=error_msg,
                finish=True,
            )
            return self._normalize(
                response,
                record.correlation_id,
                "failed",
                "",
                raw_request=body,
            )
        self.resources.stats.update(record.correlation_id, request_id=task_id, status="queued")
        return self._normalize(
            response,
            record.correlation_id,
            "queued",
            task_id,
            raw_request=body,
        )

    def status(self, request_id: str) -> Response:
        record = self.resources.stats.find_by_request_id(request_id)
        if record is None:
            record = self.resources.stats.start("status")
            self.resources.stats.update(record.correlation_id, request_id=request_id)
        response = self._request(
            "GET",
            f"/api/v1/jobs/recordInfo?{urlencode({'taskId': request_id})}",
            record.correlation_id,
            api_key=self._key_for_request(),
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
        raise CapabilityError("KIE cancellation is not documented")

    def _poll(
        self,
        task_id: str,
        correlation_id: str,
        api_key: str,
        raw_request: Any = None,
    ) -> Response:
        deadline = time.monotonic() + self.config.poll_timeout
        while time.monotonic() < deadline:
            response = self._request(
                "GET",
                f"/api/v1/jobs/recordInfo?{urlencode({'taskId': task_id})}",
                correlation_id,
                api_key,
            )
            status = self._status(response)
            self.resources.stats.update(correlation_id, status=status)
            if status in {"completed", "failed"}:
                self.resources.stats.update(correlation_id, status=status, finish=True)
                return self._normalize(
                    response,
                    correlation_id,
                    status,
                    task_id,
                    raw_request=raw_request,
                )
            time.sleep(self.config.poll_interval)
        self.resources.stats.update(correlation_id, error="polling timeout")
        raise TimeoutError(f"KIE task {task_id} polling timed out")

    def _request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        body: dict[str, Any] | None = None,
        api_key: str | None = None,
    ) -> Any:
        headers = {
            "Authorization": f"Bearer {api_key or self._key_for_request()}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
        }
        _, response = self.request_json(
            method,
            f"{self.base_url}{path}",
            body=body,
            headers=headers,
            correlation_id=correlation_id,
            operation=method,
        )
        return response

    def _prepare_media(
        self,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        correlation_id: str,
        api_key: str,
    ) -> tuple[str | None, str | None]:
        return (
            self._prepare_one_media(image, correlation_id, api_key),
            self._prepare_one_media(video, correlation_id, api_key),
        )

    def _prepare_one_media(
        self,
        media: str | os.PathLike[str] | None,
        correlation_id: str,
        api_key: str,
    ) -> str | None:
        if media is None:
            return None
        value = str(media)
        if value.startswith(("http://", "https://", "oss://")):
            return value
        return self._upload_file(value, correlation_id, api_key)

    def _upload_file(self, path: str, correlation_id: str, api_key: str) -> str:
        file_name = os.path.basename(path)
        with open(path, "rb") as media_file:
            fields = {
                "file": (file_name, media_file.read(), mimetypes.guess_type(path)[0] or "application/octet-stream"),
                "uploadPath": "media",
                "fileName": file_name,
            }
        body, content_type = encode_multipart_formdata(fields)
        self.resources.acquire()
        self.resources.stats.begin_http()
        try:
            response = self.resources.pool.request(
                "POST",
                self.upload_url,
                body=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": content_type,
                    "X-Correlation-ID": correlation_id,
                },
            )
            self.resources.stats.record_attempt(correlation_id, response.status)
            if response.status >= 400:
                raise HttpProviderError(response.status, "KIE file upload failed")
            result = self._decode(response)
            try:
                return str(result["data"]["fileUrl"])
            except (KeyError, TypeError) as error:
                raise RuntimeError("KIE upload response did not include data.fileUrl") from error
        finally:
            self.resources.stats.end_http()
            self.resources.release()

    @classmethod
    def _body(
        cls,
        model: str,
        prompt: str,
        image: str | os.PathLike[str] | None,
        video: str | os.PathLike[str] | None,
        workflow: str | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        workflow = validate_workflow_inputs(model, image, video, workflow)
        input_data = {"prompt": prompt, **kwargs}
        if workflow in {"image-to-image", "image-to-video", "edit"}:
            image_url = str(image)
            if not image_url.startswith(("http://", "https://", "oss://")):
                raise CapabilityError("KIE image workflows require a public image URL")
            if "banana" in model.lower() or "z-image" in model.lower():
                input_data["image_input"] = [image_url]
            elif "minimax" in model.lower():
                input_data["first_frame_url"] = image_url
            else:
                input_data["image_urls"] = [image_url]
        elif workflow == "video-to-video":
            video_url = str(video)
            if not video_url.startswith(("http://", "https://", "oss://")):
                raise CapabilityError("KIE video workflows require a public video URL")
            input_data["video_urls"] = [video_url]
        return {"model": model, "input": input_data}

    @staticmethod
    def _task_id(response: Any) -> str | None:
        if not isinstance(response, dict):
            return None
        data = response.get("data")
        if not isinstance(data, dict):
            return None
        task_id = data.get("taskId")
        return str(task_id) if task_id is not None else None

    @staticmethod
    def _extract_error(response: Any) -> str:
        if isinstance(response, dict):
            return str(
                response.get("msg")
                or response.get("message")
                or response.get("failMsg")
                or "KIE request failed"
            )
        return "KIE request failed"

    @staticmethod
    def _status(response: Any) -> str:
        try:
            state = str(response["data"]["state"]).lower()
        except (KeyError, TypeError):
            return "failed"
        return {
            "waiting": "queued",
            "queuing": "queued",
            "generating": "processing",
            "success": "completed",
            "fail": "failed",
        }.get(state, "processing")

    @staticmethod
    def _normalize(
        response: Any,
        correlation_id: str,
        status: str,
        request_id: str,
        raw_request: Any = None,
    ) -> Response:
        data = response.get("data") if isinstance(response, dict) else {}
        if not isinstance(data, dict):
            data = {}
        result = None
        error = response.get("msg") or response.get("message") if isinstance(response, dict) else None
        if status == "completed":
            result_json = data.get("resultJson")
            try:
                result = json.loads(result_json) if isinstance(result_json, str) else result_json
            except json.JSONDecodeError:
                result = result_json
        elif status == "failed":
            error = data.get("failMsg") or error
        return Response(
            request_id=request_id if request_id else None,
            status=status,
            result=result,
            error=str(error) if error else None,
            raw_response=response,
            correlation_id=correlation_id,
            raw_request=raw_request,
        )
