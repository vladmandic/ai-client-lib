# fal.ai API Notes

Verified: 2026-09-07

Source: https://fal.ai/docs/documentation/model-apis/overview

## API shape

- Model APIs expose HTTP endpoints and accept model-specific JSON input.
- Synchronous inference is available through direct `fal.run` calls or the queue-backed subscribe pattern.
- Queue submission is the preferred production path for asynchronous work.
- Queue requests return a request identifier that can be used to query status and retrieve the result.
- Webhooks are supported for queue requests. The caller supplies a webhook URL and fal notifies it when processing completes.
- Authentication uses `Authorization: Key <FAL_KEY>` for queue REST calls. Keep the key secret and never log it.

## Verified queue endpoints

- Submit: `POST https://queue.fal.run/{model}`.
- Status: `GET https://queue.fal.run/{model}/requests/{request_id}/status`.
- Result: `GET https://queue.fal.run/{model}/requests/{request_id}`.
- Cancel: `PUT https://queue.fal.run/{model}/requests/{request_id}/cancel`.
- Webhook: append `?fal_webhook=<url>` to the submit URL. Webhook delivery uses `status: "OK"` or `status: "ERROR"`, which differs from queue statuses.

## Media and workflows

- The platform provides image and video generation/editing model APIs.
- Model support is endpoint-specific. The model reference includes text-to-image, image-to-image/editing, text-to-video, image-to-video, and video-to-video endpoints across different models.
- Inputs generally use model-specific fields and fal-hosted/public media URLs.
- fal provides CDN/file upload facilities for using local files as model inputs. The exact upload endpoint and response shape should be confirmed for the selected implementation path.
- The adapter converts local files to data URIs by default up to `data_uri_max_bytes` (10 MB default in `ClientConfig`). Existing HTTP/HTTPS URLs and data URIs pass through unchanged.
- Banana model families (e.g. `google/nano-banana-lite/edit`) automatically format reference images in `image_urls` as a list, while other image models use `image_url`. Video inputs use `video_url`.

## Implementation mapping

- `submit`: queue submission to `POST https://queue.fal.run/{model}` followed by polling the status URL (`/status`) and fetching the completed result (`/requests/{request_id}`).
- `submit_async`: submit to `POST https://queue.fal.run/{model}?fal_webhook=<url>` and return the queued response with `request_id` immediately.
- `status`: query status via `GET /{model}/requests/{request_id}/status`, and if completed, fetch result from `GET /{model}/requests/{request_id}`.
- `cancel`: issue the documented `PUT /{model}/requests/{request_id}/cancel` request.
- Media extraction: automatically extracts media URLs from `images`, `video`, and `image` result fields, enabling lazy `.bytes` download and `.images` PIL image conversion on the `Response` object.
- Retry transient HTTP failures (408, 429, 5xx) and documented queue/busy failures using exponential backoff with jitter.

## Known gaps

- Request and response fields vary by model; provider-specific parameters are passed through `kwargs`.
- Raw CDN upload is not implemented; local files are encoded as data URIs.
- Capability checks are model-aware based on inferred or explicitly passed `workflow`.
