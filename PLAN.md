# Implementation Plan

## 1. Define the shared contract

- Add shared request, normalized response, error, and provider capability types under `cli/`.
- Add one shared configuration object for polling, retry, cleanup, and logging options.
- Add configurable media handling with `auto`, `data_uri`, and `upload` strategies; initially implement data-URI conversion and fail clearly when raw upload is unavailable.
- Add a provider-scoped HTTP pool registry so every provider has exactly one reusable `urllib3` pool shared by its client instances.
- Add a thread-safe provider statistics class and record one entry per logical request with operation, request ID, timestamps, normalized status, HTTP result code, attempts, latency, and error details.
- Use one stats record per generation job; update it for later status and cancellation operations and aggregate individual HTTP attempts in its attempt and error fields.
- Retain statistics indefinitely in memory for the current implementation; leave room for a future retention limit without changing the stats interface.
- Generate a client correlation ID before each logical request, store timestamps in UTC, measure latency with a monotonic clock, and expose serializable secret-free stats dictionaries.
- Accept an optional explicit workflow on submission to override model-name inference when a model identifier is ambiguous.
- Normalize workflow aliases `t2i`, `i2i`, `t2v`, `i2v`, and `v2v` to their canonical workflow names before provider dispatch.
- Keep the public methods consistent: `submit`, `submit_async`, `status`, and `cancel` where supported.
- Support provider URLs and local media paths.
- Add an explicit option to remove temporary provider-uploaded media after job completion without touching caller-owned files.
- Delete temporary provider-uploaded media only after a terminal `completed`, `failed`, or `cancelled` state; never delete on an uncertain timeout by default.
- Define configurable polling with a 10-minute timeout and 2-second interval by default.
- Define configurable retry behavior for transient busy, rate-limit, and server errors, with maximum attempts, initial delay, maximum delay, and jitter controls.
- Define normalized response fields: `request_id`, `status`, `result`, and `error`, while preserving the raw provider response.
- Make `cancel` return the same normalized response shape as the other request methods.
- Normalize provider statuses to `queued`, `processing`, `completed`, `failed`, or `cancelled` where possible.
- Keep API keys out of logs, exceptions, normalized responses, and validation output.
- Define provider credentials through environment variables such as `FAL_API_KEY`, `KIE_API_KEY`, `PIXVERSE_API_KEY`, and `BYTEPLUS_API_KEY`.
- Accept each provider credential as either one string or a non-empty list of strings; choose a random key for each logical request and validate that all entries are strings.
- Support key lists through the Python constructor while treating each credential environment variable as one key string.
- Reuse provider idempotency keys across retries where supported.
- Keep provider adapters stateless so one client instance can serve concurrent requests while sharing the HTTP connection pool.
- Keep one statistics collector per provider alongside its shared HTTP pool.
- Add explicit pool-registry and statistics-collector shutdown/close handling for application shutdown.
- Make the pool registry safely reusable across client instances and close pools through reference counting or an explicit application-level shutdown path.
- Keep statistics in memory only for this phase.

## 2. Add common HTTP and polling helpers

- Use `urllib3.PoolManager` for REST requests.
- Obtain the provider's pool from the provider pool registry instead of constructing a pool per request or client instance.
- Add shared JSON decoding, HTTP error handling, authentication headers, and timeout handling.
- Select one API key per logical request and reuse it across retries so key rotation distributes load without changing credentials mid-request.
- Retry transient failures such as HTTP 408, 429, and 5xx responses, plus documented provider busy errors, using randomized bounded backoff. Do not retry non-transient client errors.
- Use defaults of 3 maximum attempts, 1-second initial delay, 30-second maximum delay, and full random jitter. Honor `Retry-After` when provided.
- Add local-file upload support where the provider documents an upload endpoint.
- Pass webhook URLs through unchanged.
- Add cancellation handling and raise a capability error when a provider does not support cancellation.
- Use `srv.logger` for appropriately leveled, secret-redacted logging.
- Raise explicit capability errors instead of fabricating unsupported behavior.
- Track active HTTP calls separately from active generation jobs. Treat jobs in `queued` or `processing` as current generation requests.
- Preserve all statistics records in memory while preserving active request records until they reach a terminal state.
- Enforce configurable provider-level concurrency and rate limits before dispatching HTTP calls.
- Default provider concurrency and rate limits to unlimited until configured or verified from provider documentation.

## 3. Implement provider adapters

Create one class per provider. Each class must map the shared contract to that provider's documented API and support all workflows the provider actually exposes:

- `cli/fal.py` with `Fal`: direct or queue submission, webhook submission, status polling, and documented media inputs.
- `cli/kie.py` with `Kie`: asynchronous task creation, callback forwarding, task status polling, and result normalization.
- `cli/pixverse.py` with `Pixverse`: documented video workflows, status polling, and explicit errors for unsupported image-only or video-to-video operations.
- `cli/byteplus.py` with `BytePlus`: support the verified image-generation endpoint and Seedance video task creation, polling, and cancellation; mark webhook submission and generic file upload explicitly unsupported.

Infer the workflow from model-name tokens such as `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, and `video-to-video`; do not hard-code exact model identifiers. Provider-specific payload fields remain provider concerns, and shared `kwargs` must be forwarded unchanged where the provider accepts them.
Maintain a capability matrix covering generation modes, local uploads, webhooks, polling, cancellation, and cleanup for each provider.
Record the provider API documentation version or retrieval date in the matrix.

## 4. Add the unified client

Create `cli/client.py` with:

```python
client = Client(provider="fal", api_key="...")
```

The unified client will validate the provider name, construct the matching adapter, and forward `submit`, `submit_async`, `status`, and `cancel` calls using the same interface.
Expose `current_requests(provider)` and provider statistics queries through the unified client. Asynchronous requests remain active until a terminal status is observed through polling, cancellation, or an explicit statistics update.
Expose client correlation IDs and serializable statistics records without exposing credentials or other secrets.
Document that in-memory request counts and records are process-local.

## 5. Validate against live endpoints

Do not add mock tests. Validate the implementation with actual provider endpoints and credentials supplied securely through the environment or another secret configuration. Use inexpensive models and short video durations where possible. Keep validation requests minimal and document that they may consume credits, create media, or be subject to provider rate limits.

Validate:

- Provider selection and unknown-provider errors locally.
- Text-to-image, image-to-image, text-to-video, image-to-video, and video-to-video payloads where documented and available.
- Webhook forwarding for asynchronous requests.
- Status polling, timeout, and completed-result handling.
- Cancellation for providers that support it, plus clear capability errors otherwise.
- Retry behavior for provider busy, rate-limit, and server errors where safely reproducible.
- HTTP and provider error decoding without exposing API keys.
- URL and local-path media inputs.
- Optional cleanup of provider-uploaded temporary media without deleting caller-owned files.
- Explicit failures for unsupported provider capabilities.
- Concurrent requests through one client instance without shared mutable request state.
- Shared pool reuse per provider across client instances.
- Thread-safe statistics recording and current-request counts per provider.
- Indefinite in-memory statistics retention and clean shutdown of shared pools and collectors.
- Correlation ID generation, UTC timestamps, monotonic latency measurement, and serializable stats export.
- Provider-level concurrency and rate-limit enforcement.

## 6. Document limitations and usage

Add concise usage examples and a provider capability matrix. Record any workflow that cannot be implemented due to missing documentation, unavailable API access, or provider limitations.

## 7. Validate

Run all commands with the repository virtual environment activated:

```bash
ruff check srv/* cli/*
pylint srv/* cli/*
```

Also run live provider validation for every supported adapter and an offline import smoke test for the public client and provider classes. Do not report a provider as complete until its documented supported workflows have been exercised against the real endpoint.