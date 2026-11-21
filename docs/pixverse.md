# PixVerse API Notes

Verified: 2026-09-07; C1, fusion, upload-by-URL and webhooks re-verified 2026-11-21

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

## Workflows and endpoints

The workflow is named in the model id; PixVerse receives the part before it
(`c1/reference-to-video` sends `model: "c1"`).

| Model id | Endpoint | Image inputs |
| --- | --- | --- |
| `c1`, `c1/text-to-video` | `POST /video/text/generate` | none |
| `c1/image-to-video` | `POST /video/img/generate` | `img_id`, or `image_url` (uploaded for you) |
| `c1/transition` (`c1/first-last-frame`) | `POST /video/transition/generate` | `first_frame_img`/`last_frame_img`, or `first_frame_url`/`last_frame_url` |
| `c1/reference-to-video` (`c1/fusion`) | `POST /video/fusion/generate` | `image_references[]` of `{type: subject\|background, ref_name, img_id\|image_url}` (1-10); mention refs in the prompt as `@ref_name` |

C1 (capability map): duration 1-15 s, quality `360p`/`540p`/`720p`/`1080p`,
aspect ratios `16:9 9:16 4:3 3:4 1:1 2:3 3:2 21:9` (fusion also `auto`; the img and
transition bodies take no aspect ratio). Pricing is per generated second
(C1, audio off: 6/8/10/19 credits per second at 360p/540p/720p/1080p).

## Image upload

`POST /image/upload`, multipart, either `image` (file) or `image_url` (the URL
must serve `image/jpeg|png|webp`, not `application/octet-stream`; < 20 MB,
<= 10,000 px a side). Returns `Resp.img_id`. Ids only work on the account that
made them, so the adapter uploads on the same key that then submits.
`upload_image_url()` / `upload_image_file()` expose it directly.

## Implementation mapping

- `submit`: builds the body (uploading image URLs), drops any `webhook_id`, posts, and polls `GET /video/result/{video_id}`.
- `submit_async`: same body plus `webhook_id`. PixVerse has no per-request callback URL: callbacks go to the webhook registered at `platform.pixverse.ai/webhook`, referenced by its id. The id comes from the `webhook_id` kwarg, the `webhook_id=` constructor argument or `PIXVERSE_WEBHOOK_ID`; without one it raises `CapabilityError`. The `webhook` URL argument is ignored.
- `status`: `GET /video/result/{video_id}`; `1` -> `completed` (only once `Resp.url` is set), `5` -> `processing`, `7` -> `failed` (moderation), `8` -> `failed`.
- `cancel`: raises `CapabilityError` (not documented).
- Errors: PixVerse returns most failures as HTTP 200 with a non-zero `ErrCode`. Those raise `HttpProviderError` with a mapped status: 401 auth (10001-10005, ...), 402 insufficient balance (500090), 404 not found / other account (500008, 500085, 701009), 429 busy (500044 concurrency, 500069, 712008), 422 bad input or moderation (400017, 500052/54/63, ...), else 502.

## Webhook callbacks

PixVerse POSTs JSON such as `{"id": "...", "status": 1, "url": "...", "has_audio": true, "credits": 100}`
with headers `Webhook-Timestamp`, `Webhook-Nonce`, `Webhook-Signature`, `Ai-trace-id`.
Signature = base64(HMAC-SHA256(secret, "{timestamp}\n{nonce}\n{payload}")) where the
payload is the body's fields sorted by key, booleans lowercased, encoded as a query
string (`urlencode(..., safe="")`). `verify_webhook_signature()` implements it and
rejects timestamps more than 5 minutes off. Reply HTTP 200 with body `ok`, or
PixVerse retries (2 s, 10 s, 30 s, 1 min, 5 min, 15 min, 1 h, 4 h). Check the body's
`status`, not delivery, for success.

## Known gaps

- No sub-account or billing tag is documented. Separate billing (for example free campaign videos) means a separate PixVerse account: its own API key and its own registered webhook (gateway pool `free_video`).
- Video references (V6 omni only), video-to-video, cancellation and text-to-image are not supported.
- Not live-tested yet for `image-to-video`, `transition`, `reference-to-video` or webhooks (unit tests only, `test/test_pixverse_adapter.py`).
- The capability docs do not state C1's maximum number of image references (10 is stated for V6 omni).
