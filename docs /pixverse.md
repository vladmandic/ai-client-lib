# PixVerse API Notes

Verified: 2026-09-07

Source: https://docs.platform.pixverse.ai/

Verified model workflow pages:

- [Text-to-video](https://docs.platform.pixverse.ai/text-to-video-882970m0)
- [Image-to-video](https://docs.platform.pixverse.ai/image-to-video-882971m0)

## API shape

- PixVerse is primarily a video generation API platform.
- The documented feature set includes text-to-video and image-to-video, plus templates/effects, multimodal references, frame transition, and related video features.
- The documentation provides an API overview, parameter reference, API-key guide, and a video-generation-status guide.
- Generation is task-oriented: create a video task, then retrieve its generation status/result.
- Authentication and exact request headers must be taken from the API-key and quick-start documentation.
- Verified API base: `https://app-api.pixverse.ai/openapi/v2`.
- Text generation endpoint: `POST /video/text/generate`.
- Image generation endpoint: `POST /video/img/generate`.
- Result endpoint: `GET /video/result/{video_id}`.
- Requests require `API-KEY` and a unique `Ai-trace-id`; reuse the same trace ID for status polling for one generation job.

## Media and workflows

- Text-to-video is documented.
- Image-to-video is documented.
- Image references and multimodal references are supported for some video features.
- Image-only generation is not established by the platform overview.
- Video-to-video is not established by the platform overview and must not be advertised by the adapter without endpoint-level confirmation.
- Image-to-video generation uses an uploaded `img_id`; local image upload is `POST /image/upload` as multipart form data. The adapter currently requires the resulting `img_id` in `kwargs` rather than hiding upload state.

## Implementation mapping

- `submit`: validates workflow (`text-to-video` or `image-to-video`), dispatches to `POST /video/text/generate` or `POST /video/img/generate` using generated `Ai-trace-id`, and polls `GET /video/result/{video_id}` until completed or failed.
- `submit_async`: raises `CapabilityError("PixVerse callback/webhook submission is not documented")`.
- `status`: queries `GET /video/result/{video_id}` with `Ai-trace-id` and maps status codes (1 -> `completed`, 5 -> `processing`, 7/8 -> `failed`).
- `cancel`: raises `CapabilityError("PixVerse cancellation is not documented")`.
- Media extraction: extracts media URLs from `Resp.video_url` or related fields, enabling lazy `.bytes` download on the `Response` object.

## Known gaps

- Workflow inference extracts the model name prefix before the workflow token (e.g. `v4.5/image-to-video` sends `model="v4.5"`).
- Image-to-video requires an uploaded image ID (`img_id`) passed in `kwargs`.
- Text-to-image, image-to-image, video-to-video, async webhook callbacks, and task cancellation are not supported by the documented API and raise `CapabilityError`.
- Status codes: `1` success, `5` in progress, `7` moderation failure, and `8` generation failure.
