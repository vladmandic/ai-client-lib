# Unified Media Generation Client

Python 3.12+ client library for image and video generation providers. The client uses raw `urllib3` HTTP requests and exposes one provider-independent facade.

## Status

Capabilities are inferred from workflow tokens in the model name. Exact model identifiers are not hard-coded. Provider documentation and endpoint availability still determine whether a workflow can run.

| Provider | Workflows currently supported | Unsupported | Unclear or not verified |
| --- | --- | --- | --- |
| fal.ai | `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, `video-to-video` when the selected fal model exposes that endpoint; submit, async webhook, status/polling, cancel | Local paths in the current adapter; upload/delete lifecycle is not wired into the adapter | Exact supported workflow depends on the selected model and its schema |
| KIE | Model-name-derived `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, `video-to-video`; local file upload; synchronous polling and async callback submission | `cancel`; models whose names do not contain a supported workflow token | The verified schemas are Seedream 5 Pro text-to-image and Kling 3.0 Omni image-to-video; other model-specific fields and media conventions must be checked against their model pages |
| PixVerse | `text-to-video` and `image-to-video`; synchronous submission and status polling | `text-to-image`, `image-to-image`, `video-to-video`, async webhook submission, cancellation; local image paths unless uploaded first | Model-specific parameters, upload cleanup, plans, credits, and rate limits |
| BytePlus | Image `submit`; Seedance-style video `submit`, polling/status, cancel/delete; explicit Files API upload/retrieve/delete methods | `submit_async` webhooks; automatic File ID insertion into generation payloads | Exact capabilities vary by selected ModelArk model; Seedance 2.5 has strict reference/task constraints |

This project has not performed live provider validation in the repository. Live calls require credentials and may consume credits or create media.

## Public API

```python
from cli import Client, ClientConfig

config = ClientConfig(
    poll_timeout=600,
    poll_interval=2,
    max_attempts=3,
    retry_initial_delay=1,
    retry_max_delay=30,
)

client = Client(provider="fal", api_key="...", config=config)
response = client.submit(
    model="some-model/text-to-image",
    prompt="a mountain lake at sunrise",
    width=1024,
    height=1024,
)
print(response.status, response.result)
client.close()
```

The shared methods are:

- `submit(...)`: submit and poll until completion.
- `submit_async(..., webhook=...)`: submit and return without waiting.
- `status(request_id, ...)`: retrieve normalized status and result data.
- `cancel(request_id, ...)`: cancel when the provider documents cancellation.
- `current_requests()`: count queued or processing generation jobs for the provider.
- `active_http_requests()`: count active HTTP calls for the provider.
- `records()`: return secret-free, serializable in-memory request statistics.

## Webhook endpoint

The server exposes a provider-agnostic webhook receiver at:

```text
POST /api/webhook
```

Use the public server URL as the provider callback URL, for example:

```text
https://your-host.example/api/webhook
```

The endpoint accepts provider JSON payloads, downloads common media URL fields, and stores the event plus saved paths in process-local server state. Files are saved under `WEBHOOK_MEDIA_DIR` (default: `media`) using `provider-request_id` as the filename stem. Multiple media items receive an index suffix. The endpoint returns `202 Accepted` immediately. It does not yet verify provider signatures or dispatch results into client statistics; provider-specific verification and processing remain application responsibilities.

All responses contain `request_id`, `status`, `result`, `error`, `raw_response`, and `correlation_id` where available. Normalized statuses are `queued`, `processing`, `completed`, `failed`, and `cancelled`.

## Workflow inference

The adapter infers workflows from model-name tokens where available:

- `text-to-image`
- `image-to-image`
- `edit`
- `text-to-video`
- `image-to-video`
- `video-to-video`

If a model name has no workflow token, the default is `text-to-image` without media, `image-to-image` with an image, or `video-to-video` with a video. Provider-specific model schemas may still require fields such as `image_input`, `image_urls`, `first_frame_url`, or `last_frame_url`.

When model-name inference is ambiguous, pass `workflow` explicitly:

```python
client.submit(
    model="provider/custom-model",
    workflow="image-to-video",
    prompt="animate the subject",
    image="https://example.com/reference.jpg",
)
```

Valid values are `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, and `video-to-video`.

Aliases are also accepted: `t2i`, `i2i`, `t2v`, `i2v`, and `v2v`.

For example:

```python
client.submit(
    model="provider/v4/image-to-video",
    prompt="a slow camera move through a forest",
    image="https://example.com/reference.jpg",
)
```

Provider-specific options are passed through `kwargs`. The model name determines the expected standard media inputs, but it does not guarantee that the provider has a matching endpoint.

## Credentials

Credentials can be passed as one string or a non-empty list of strings:

```python
Client(provider="fal", api_key=["key-a", "key-b"])
```

A random key is selected once per logical request and reused for that request's retries. Environment variables represent one key each:

- `FAL_API_KEY`
- `KIE_API_KEY`
- `PIXVERSE_API_KEY`
- `BYTEPLUS_API_KEY`

Keys are never intended to appear in logs, exceptions, normalized responses, or statistics.

## Provider details

- [fal.md](fal.md): queue endpoints, webhooks, cancellation, CDN inputs, and model-dependent workflows.
- [kie.md](kie.md): KIE Market task creation, callbacks, polling, and verified example schemas.
- [pixverse.md](pixverse.md): text/image-to-video endpoints, image upload, trace IDs, and numeric statuses.
- [byteplus.md](byteplus.md): ModelArk overview and unresolved endpoint requirements.

## Shared infrastructure

- One reusable `urllib3.PoolManager` and statistics collector per provider, shared across client instances.
- Configurable retries with randomized bounded backoff for transient errors such as 408, 429, 5xx, and documented busy responses.
- Configurable provider concurrency and rate limits; defaults are unlimited until configured.
- Thread-safe, process-local, in-memory statistics retained indefinitely for now.
- Explicit `close()` and `Client.close_all()` lifecycle methods.
- Logging uses `srv.logger` and must remain secret-redacted.

## Important limitations

- Provider payload fields are model-specific. Do not assume `width`, `height`, media field names, or output schemas work for every model.
- Local file support is provider-specific. URLs are the portable media input format.
- Fal local files use data URIs by default when they are within the configured size limit. Configure `ClientConfig(media_strategy="data_uri")` to force conversion or `media_strategy="upload"` when a provider upload implementation is available.
- Async jobs remain active in local statistics until a terminal status is observed through polling, cancellation, or an explicit stats update.
- Retries of task creation can duplicate jobs when a provider does not support idempotency keys. Configure retries carefully for such endpoints.
- Generated media URLs can expire according to provider retention policies. Download important results promptly.
- `current_requests()` and statistics are process-local; they are not a distributed queue or metrics system.

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Validation

```bash
source venv/bin/activate
ruff check srv/* cli/* test/*
pylint srv/* cli/* test/*
python -m compileall -q cli
python -m compileall -q srv
python -m compileall -q test
```

Live provider validation is intentionally separate from static validation and requires real credentials. Use inexpensive models and short videos where possible.
