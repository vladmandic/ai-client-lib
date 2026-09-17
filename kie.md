# KIE API Notes

Verified: 2026-09-07

Source: https://docs.kie.ai/

Verified model examples:

- [Seedream5.0 Pro - Text to Image](https://docs.kie.ai/market/seedream/5-pro-text-to-image)
- [Kling 3.0 Omni Image To Video](https://docs.kie.ai/market/kling/v3-omni-image-to-video)

## API shape

- All generation tasks are asynchronous.
- Requests use JSON with `Authorization: Bearer <API_KEY>` and `Content-Type: application/json`.
- Successful task creation returns HTTP 200 and a `task_id`; HTTP 200 means the task was created, not completed.
- Results are obtained either through a callback URL supplied in the request or by polling the query-record-info API with the task ID.
- Generated media is retained for 14 days; log metadata is retained for 2 months.
- The documented default limit is up to 20 new generation requests per 10 seconds, with commonly more than 100 concurrent running tasks. HTTP 429 requests are rejected and do not enter the queue.
- Verified server: `https://api.kie.ai`.
- Verified create endpoint: `POST /api/v1/jobs/createTask`.
- Verified task details endpoint: `GET /api/v1/jobs/recordInfo?taskId=<task_id>`.
- Creation response uses `data.taskId`.

## Media and workflows

- KIE exposes multiple model APIs through its market/playground. Exact parameters and output formats are model-specific.
- The general documentation confirms asynchronous image/video generation tasks, but the common guide does not establish that every requested workflow is available for every model.
- Local paths are uploaded through `POST https://kieai.redpandaai.co/api/file-stream-upload`; the returned `data.fileUrl` is passed to model generation. Uploaded files are temporary and should be downloaded or migrated before expiry.

## Verified capability examples

- `seedream/5-pro-text-to-image`: demonstrates the text-to-image schema: a text `prompt` plus model-specific fields such as `aspect_ratio`, `quality`, and `output_format`. The adapter infers this workflow from the model name rather than matching this exact identifier.
- `kling-3.0-omni/image-to-video`: demonstrates the image-to-video schema: a text `prompt` and exactly one image URL in `input.image_urls`; HTTP, HTTPS, and OSS URLs are accepted. The adapter infers this workflow from the model name rather than matching this exact identifier.
- `nano-banana-2`: demonstrates an image-generation model whose name does not contain a workflow token; with no media input it defaults to text-to-image, and reference images use `input.image_input`.
- `z-image`: demonstrates an image-generation model whose name does not contain a workflow token; with no media input it defaults to text-to-image.
- `pixverse-v6/text-to-video`: confirms the generic text-to-video task shape and fields such as `aspect_ratio`, `quality`, `duration`, and audio/multi-clip switches.
- `pixverse-v6/image-to-video`: confirms image-to-video with `input.image_urls`, up to two HTTP/HTTPS/OSS image URLs, and video options such as duration and quality.
- `minimax-h3/text-to-video`: confirms text-to-video fields including required `aspect_ratio` and duration.
- `minimax-h3/image-to-video`: confirms image-to-video using `first_frame_url` and/or `last_frame_url`, rather than `image_urls`.
- Both examples accept an optional `callBackUrl` and can be polled through the unified task-details endpoint.

## Implementation mapping

- `submit`: create the task, then poll task details until a terminal state.
- `submit_async`: create the task with the caller's callback URL unchanged and return the task ID.
- `status`: query task details and normalize the provider status/result.
- `cancel`: cancellation is not established by the general or example model documentation; keep it unsupported.
- Use the documented bearer authentication and retry 429/transient server responses with the configured backoff.

## Known gaps

- The two pages are schema examples, not an allowlist. Any KIE model whose name contains a supported workflow token is validated generically; provider-specific fields remain in `kwargs`.
- Models without a recognizable workflow token default to text-to-image when no media is supplied, image-to-image when an image is supplied, and video-to-video when a video is supplied.
- KIE image schemas vary by model family: Banana models use `image_input`, MiniMax H3 uses frame URL fields, and other image-to-video models use `image_urls`. Provider-specific kwargs remain the escape hatch for additional fields.
- Local files are supported through the KIE File Upload API; remote URLs continue to pass through unchanged.
- Avoid retrying task creation without an idempotency mechanism because a retry may create a duplicate task.
