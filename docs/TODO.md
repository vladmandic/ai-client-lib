# Open Items

## Status and validation

- Live smoke tests executed and verified for Fal (`t2i`, `i2i`), KIE (`t2i`, `i2i`), BytePlus (`t2i`, `i2i`), and PixVerse (`t2v`) under `test/*.md`.
- PixVerse image-to-video (`i2v`) live validation requires testing with pre-uploaded `img_id`.
- Confirm provider response schemas, status transitions, retry behavior, rate limits, and result URL expiration in live calls.
- Reconcile any live API differences with the provider notes and capability matrix.

## Provider gaps

### Fal

- Implement raw Fal CDN upload strategy if needed for `ClientConfig(media_strategy="upload")` (currently uses data URIs up to configured size limit).
- Add optional cleanup for provider-uploaded Fal assets after terminal job states.
- Verify data-URI acceptance across video models and very large files.
- Verify idempotency behavior for task creation retries.

### KIE

- Add cancellation if KIE documents a cancellation endpoint (currently unsupported).
- Confirm KIE upload expiration/cleanup behavior in live use and document any provider-specific file limits.
- Add model-specific schema validation for additional model families while preserving passthrough `kwargs`.
- Prevent duplicate task creation on retries when an idempotency mechanism is unavailable.

### PixVerse

- Implement native async callback handling if the PixVerse API documents webhook submission.
- Implement cancellation if the PixVerse API documents it.
- Add local image upload handling instead of requiring callers to provide `img_id` in `kwargs`.
- Verify model-specific parameter constraints, account limits, and result URL retention.

### BytePlus

- Verify whether Seedance generation accepts Files API IDs directly; currently File IDs are exposed through explicit methods but not automatically inserted into generation content.
- Add automatic File API asset cleanup after terminal jobs once generation payload integration is verified.
- Add model-specific validation for Seedream image generation and Seedance video task constraints.
- Support additional ModelArk regions through configuration and validate region/model compatibility.

## Webhook hardening

- Verify provider webhook signatures before accepting or processing events:
  - Fal signed webhook headers and JWKS verification.
  - KIE callback verification if required by the selected model/API.
  - Any documented PixVerse or BytePlus verification scheme.
- Dispatch accepted webhook events into the matching client/provider statistics record.
- Add a stable correlation mapping from provider request/task IDs to local records.
- Move media downloading out of the request path or otherwise guarantee the webhook responds within provider timeout limits.
- Add SSRF protection for downloaded media URLs, including allowed schemes, private-address blocking, redirect policy, and maximum response size.
- Validate downloaded media content types and extensions before saving.
- Make webhook media storage configurable with retention/cleanup policy and collision handling.
- Ensure webhook event persistence and media saves are safe across concurrent requests.

## Shared client hardening

- Add a documented provider capability matrix that matches the current adapter behavior rather than only the source documentation.
- Add provider-specific default concurrency and rate-limit settings once verified from live accounts/docs.
- Add idempotency-key configuration and propagation for providers that support it.
- Define behavior for process shutdown while asynchronous jobs are still active.
- Confirm that shared pool reference counting remains correct when `Client.close_all()` is used.
- Decide whether `current_requests()` should expose records for unknown or expired provider jobs.

## Validation and maintenance

- Keep live smoke commands or scripts for each provider outside the library's automated test suite.
- Test webhook payloads from each provider against `/api/webhook`.
- Verify saved filenames and media extensions for single and multiple webhook media outputs.
- Re-run `ruff check srv/* cli/*`, `pylint srv/* cli/*`, and package compilation after each provider change.
- Keep `README.md`, `TASK.md`, `PLAN.md`, and provider notes synchronized with actual support status.
