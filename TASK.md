# Unified Media Generation Client

Implement a unified Python 3.12+ client library for image and video generation across multiple providers.

## Requirements

The client library must use `urllib3` for HTTP REST requests and expose the following standard methods for each provider:

- `submit`: submit a request and wait until the result is ready.
- `submit_async`: submit a request with a webhook URL and return immediately. The caller owns the webhook and handles the result.
- `status`: check the status of a request and return the result when it is ready.
- `cancel`: cancel a submitted request when the provider supports cancellation.

Synchronous polling must use a configurable timeout and polling interval. The defaults are 10 minutes and 2 seconds.

Polling, retry, cleanup, and logging options must be grouped in a shared configuration object rather than duplicated across provider method signatures.

Media handling must support a configurable strategy: `auto` uses data URIs for local files up to a configured size limit, `data_uri` forces data-URI conversion, and `upload` uses a provider upload endpoint when implemented. URLs and existing data URIs pass through unchanged.

Maintain one shared `urllib3` HTTP pool per provider. Provider client instances must reuse the pool for that provider rather than creating a new pool per request or per instance.

HTTP requests must support configurable retries for transient busy or server errors, including rate limiting and provider/server errors where retrying is appropriate. Retry behavior must use randomized backoff and expose configuration for the maximum attempts, initial delay, maximum delay, and jitter. Non-transient client errors must fail immediately.

Each provider must be implemented as a separate file and class, for example: `cli/fal.py:Fal`.

each provider should be implemented as a separate file and class, for example: `cli/fal.py:Fal`

Standard parameters for submit requests:
- provider api key: a string or a non-empty list of strings. When a list is provided, select one key at random for each logical request to distribute load across keys.
- model name
- optional workflow (`text-to-image`/`t2i`, `image-to-image`/`i2i`, `edit`, `text-to-video`/`t2v`, `image-to-video`/`i2v`, or `video-to-video`/`v2v`) to override model-name inference
- async flag (`true`/`false`)
- image or video prompt
- optional image for image-to-image or image-to-video
- optional video for video-to-video
- `kwargs`: a dictionary passed to the provider API unchanged, for example: `{"width": 512, "height": 512}`

Image and video inputs may be provider URLs or local file paths. Local files must be uploaded through a documented provider upload endpoint where available. If a provider does not support the required upload or workflow, the client must raise a clear capability error and document the limitation.

When local media is uploaded, the client may optionally delete the temporary provider-uploaded asset after the generation job completes. It must never delete or modify the caller's original local file.

Provider methods must return normalized common fields together with the raw provider response, preserving provider-specific data.

The `cancel` method must return the same normalized response shape as other request methods. If cancellation is unsupported, it must raise a clear capability error.

The normalized response must include stable `request_id`, `status`, `result`, and `error` fields. Provider statuses must be mapped to `queued`, `processing`, `completed`, `failed`, or `cancelled` where possible.

Introduce a provider statistics class that records each logical request, including operation, request ID, timestamps, status, HTTP result code, attempt count, latency, and error information when available. Statistics access must be safe for concurrent requests and must not expose API keys.

Use one statistics record per generation job. Status and cancellation operations update that record, while individual HTTP attempts are aggregated in its attempt count and error fields.

Statistics must be retained indefinitely in memory for now. Shared provider pools and statistics collectors must expose an explicit close or shutdown path for clean resource release. A future retention limit may be added without changing the stats interface.

Each logical request must receive a client-generated correlation ID before the provider request begins. Timestamps must be stored in UTC, while latency must use a monotonic clock. Statistics must be exportable as serializable, secret-free dictionaries.

Retry defaults are 3 maximum attempts, a 1-second initial delay, a 30-second maximum delay, and randomized full jitter. The client must honor a provider `Retry-After` value when present. API keys must never appear in logs, exceptions, normalized responses, or validation output.

submit requests should be able to handle:
- text-to-image
- image-to-image
- text-to-video
- image-to-video
- video-to-video

do not create separate classes for each type of request, instead use a single class per provider that can handle all types of requests based on the input parameters.

Target providers:
- [fal.ai](https://fal.ai/docs/documentation/model-apis/overview)
- [kie.ai](https://docs.kie.ai/)
- [pixverse](https://docs.platform.pixverse.ai/)
- [byteplus](https://ai.byteplus.com/ark/region:ap-southeast-1/docs/ModelArk/1099455)

Provider capabilities must be based on the documented APIs. Do not simulate unsupported webhook, polling, media upload, or generation behavior.

Maintain a capability matrix for each provider and workflow. Provider model names and payload construction remain provider-specific.

When all provider adapters are complete, create a unified `Client` class that can be used with the same interface, for example: `Client(provider="fal", api_key="...")`. It must select the provider class and forward calls to it.

Do not create separate classes for text-to-image, image-to-image, text-to-video, image-to-video, or video-to-video. One class per provider must handle all supported request types based on the input parameters.

## Scope decisions

- Public method names are `submit`, `submit_async`, `status`, and `cancel`.
- `cancel` is also part of the shared interface where the provider supports it; unsupported cancellation must raise a clear capability error.
- Webhook URLs are passed through unchanged; webhook server implementation is out of scope.
- Provider-specific `kwargs` are passed through unchanged.
- Transient HTTP failures use configurable retries with randomized backoff; non-retryable failures are returned immediately.
- Normalized responses include `request_id`, `status`, `result`, and `error`, while preserving the raw provider response.
- Provider status values are normalized to `queued`, `processing`, `completed`, `failed`, or `cancelled` where possible.
- Retry defaults are 3 attempts, 1-second initial delay, 30-second maximum delay, and full random jitter; `Retry-After` is honored when provided.
- API keys must not be exposed in logs, exceptions, normalized responses, or validation output.
- Use the existing `srv.logger` logging implementation; logging must be opt-in or appropriately leveled and must redact secrets.
- Support provider credentials through documented environment variables such as `FAL_API_KEY`, `KIE_API_KEY`, `PIXVERSE_API_KEY`, and `BYTEPLUS_API_KEY`.
- Where providers support idempotency keys, retries must reuse the same key to avoid duplicate generation jobs.
- When a list of API keys is supplied, select the key once per logical request and reuse that key for all retries of the request.
- Support API-key lists through the Python constructor; environment variables represent one key each and do not require list parsing.
- Optionally remove temporary provider-uploaded media after job completion; never remove caller-owned source files.
- Cleanup is performed only after a terminal `completed`, `failed`, or `cancelled` state. An uncertain timeout must not trigger cleanup unless explicitly requested.
- Use inexpensive models and short video durations for live validation where possible.
- Record the provider API documentation version or retrieval date in the capability matrix.
- Client instances should be safe for concurrent requests and remain stateless apart from shared HTTP connection pooling.
- Maintain one shared HTTP pool and one statistics collector per provider across client instances.
- Expose queries for current generation requests by provider, including at least `current_requests(provider)` and the underlying request records. Current generation requests are requests whose normalized status is `queued` or `processing`; active HTTP calls should be tracked separately when needed.
- For asynchronous jobs, keep a request active until a terminal status is observed through polling, cancellation, or an explicit stats update.
- Retain statistics indefinitely in memory for the current implementation; do not add persistent metrics storage.
- Provide an explicit way to close shared provider HTTP pools and statistics resources during application shutdown.
- Manage shared provider pools with a registry that supports safe reuse and reference-counted or application-level shutdown.
- Support configurable provider-level concurrency and rate limits.
- Provider concurrency and rate limits default to unlimited until configured or verified from provider documentation.
- Keep statistics history in memory only; persistent metrics storage is out of scope.
- Because statistics are in memory, request counts and records are process-local.
- No provider SDKs are required; use raw `urllib3` requests.
- Do not write mock tests. Validation must use the actual provider endpoints with real credentials supplied through the environment or another secure configuration.
- Live validation must be performed carefully because provider requests may consume credits, be rate-limited, or create real media.
- Any provider or workflow that cannot be completed because of documentation, API, or capability limits must be marked clearly in the documentation and final implementation report.

BytePlus support is based on the verified image-generation and Seedance video task tutorials: image submission, video submission with polling, status, and documented queued-task cancellation are supported; webhook submission and generic file upload remain unsupported.

ask any clarifying questions before starting the implementation.
if any provider cannot be completed due to lack of documentation or api access, mark it as such.
