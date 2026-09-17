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

- `submit`: infer `text-to-video` or `image-to-video` from the model name, create the corresponding task, and poll its result endpoint.
- `submit_async`: callback/webhook submission is not documented on these pages; report unsupported rather than simulating it.
- `status`: query the documented video-generation status endpoint and normalize the task state/result.
- `cancel`: not established by the overview; keep unsupported until verified in the API reference.

## Known gaps

- The adapter infers workflow from model-name tokens; the API model value is the portion before the final workflow token, for example `v4.5/image-to-video` sends `v4.5`.
- Status values are `1` success, `5` in progress, `7` moderation failure, and `8` generation failure.
- Video-to-video, callbacks, and cancellation remain unsupported by these pages.
- API plans, credits, rate limits, and output retention must be checked before live validation.
