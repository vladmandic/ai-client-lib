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
- The adapter currently converts local files to data URIs by default up to its configured limit. Existing URLs and data URIs pass through unchanged; raw CDN upload remains a separate strategy pending endpoint-level verification.

## Implementation mapping

- `submit`: use synchronous/direct inference where appropriate, or queue submission followed by status polling.
- `submit_async`: submit to the queue with the caller's webhook URL unchanged.
- `status`: query the queue status and fetch the completed result using the provider request ID.
- `cancel`: issue the documented `PUT` cancellation request. `202` means cancellation requested; `400` may mean already completed; `404` means not found.
- Retry transient HTTP failures and documented queue/busy failures. Preserve the selected API key and idempotency behavior across retries where supported.

## Known gaps

- Request and response fields vary by model; do not invent one universal provider payload.
- Exact generic cancellation endpoint and generic upload/delete lifecycle need endpoint-level verification.
- Capability checks must be model-aware even though the adapter is one class.
- Provider concurrency limits are documented separately and should be configured rather than assumed unlimited.
