# Unified Media Generation Client

Python 3.12+ client library for image and video generation providers. The client uses raw `urllib3` HTTP requests and exposes one provider-independent facade.

## Status

Capabilities are inferred from workflow tokens in the model name or specified via the `workflow` argument. Exact model identifiers are not hard-coded. Provider documentation and endpoint availability determine whether a workflow can run.

| Provider | Workflows currently supported | Unsupported | Verified / Implementation details |
| --- | --- | --- | --- |
| fal.ai | `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, `video-to-video`; synchronous `submit` (with polling), async `submit_async` (`?fal_webhook=`), `status`, `cancel` | Raw CDN upload endpoint (uses data URIs for local files) | Uses queue endpoints `POST /{model}`, status polling `GET /{model}/requests/{request_id}/status`, result retrieval `GET /{model}/requests/{request_id}`, cancel `PUT /{model}/requests/{request_id}/cancel`. Auto-formats Banana models (`image_urls` list) vs single `image_url`. |
| KIE | `text-to-image`, `image-to-image`, `edit`, `text-to-video`, `image-to-video`, `video-to-video`; synchronous `submit` (with polling), async `submit_async` (`callBackUrl`), `status` | `cancel` (cancellation is not documented by KIE) | Uses `POST /api/v1/jobs/createTask` and status polling `GET /api/v1/jobs/recordInfo?taskId=`. Automatically uploads local media files to `POST https://kieai.redpandaai.co/api/file-stream-upload`. Handles model-specific schemas (Seedream defaults, Banana/z-image `image_input`, MiniMax `first_frame_url`, other `image_urls`/`video_urls`). |
| PixVerse | `text-to-video`, `image-to-video`; synchronous `submit` (with polling), `status` | `text-to-image`, `image-to-image`, `video-to-video`, `submit_async` (webhooks), `cancel` | Uses `POST /video/text/generate` and `POST /video/img/generate`, status polling `GET /video/result/{video_id}` with `Ai-trace-id`. Image-to-video requires an uploaded `img_id` passed in `kwargs`. |
| BytePlus | Image workflows (`text-to-image`, `image-to-image`, `edit`) via synchronous `submit`; Seedance video workflows (`text-to-video`, `image-to-video`, `video-to-video`) via `submit` (with polling), async `submit_async` (`callback_url`), `status`, `cancel`; ModelArk Files API (`upload_file`, `upload_url`, `get_file`, `delete_file`) | Image `submit_async` webhooks (image generation is synchronous); local video files (video inputs require public URLs) | Uses ModelArk `POST /images/generations` for image workflows and `POST /contents/generations/tasks` for Seedance video tasks. Files API methods available on `BytePlus` adapter. Configurable `base_url`. |

## Public API

### Basic Usage

```python
from cli import Client, ClientConfig

config = ClientConfig(
    poll_timeout=600.0,
    poll_interval=2.0,
    max_attempts=3,
    retry_initial_delay=1.0,
    retry_max_delay=30.0,
    retry_jitter=1.0,
    concurrency_limit=5,
    requests_per_second=2.0,
    media_strategy="auto",
    data_uri_max_bytes=10 * 1024 * 1024,
)

with Client(provider="fal", api_key="...", config=config) as client:
    response = client.submit(
        model="fal-ai/z-image/turbo",
        prompt="a mountain lake at sunrise",
        image_size="portrait_16_9",
    )
    print(f"Status: {response.status}")
    print(f"Media URL: {response.media_url}")
    
    # Access downloaded bytes or PIL Images
    raw_bytes = response.bytes       # BytesList of media items
    images = response.images         # ImagesList of PIL.Image objects
    if images:
        images[0].save("output.png")
```

### Shared Client Methods

- `client.submit(model, prompt, image=None, video=None, workflow=None, **kwargs) -> Response`: Submit a request and poll until completion or failure.
- `client.submit_async(model, webhook, prompt=None, image=None, video=None, workflow=None, **kwargs) -> Response`: Submit an asynchronous request with a webhook URL and return the queued response immediately without polling.
- `client.status(request_id, ...) -> Response`: Query status and fetch results for a task.
- `client.cancel(request_id, ...) -> Response`: Cancel a task when supported by the provider.
- `client.current_requests() -> int`: Count queued or processing generation jobs for the provider.
- `client.active_http_requests() -> int`: Count active HTTP network requests for the provider.
- `client.records() -> list[dict[str, Any]]`: Return in-memory request tracking records for statistics and auditing.
- `client.close() -> None`: Release provider pool and resources for this client instance.
- `Client.close_all() -> None`: Static method to release all provider resources across the entire process.

### Direct Provider Adapters

Direct provider classes can also be instantiated directly:

```python
from cli import Fal, Kie, Pixverse, BytePlus

fal_client = Fal(api_key="...")
kie_client = Kie(api_key="...")
pixverse_client = Pixverse(api_key="...")
byteplus_client = BytePlus(api_key="...", base_url="https://ark.ap-southeast.bytepluses.com/api/v3")
```

#### BytePlus Files API

The `BytePlus` adapter includes explicit methods for the ModelArk Files API:

```python
# Upload local file
file_info = byteplus_client.upload_file("path/to/image.jpg", purpose="user_data")

# Upload public URL
file_info = byteplus_client.upload_url("https://example.com/asset.png", purpose="user_data")

# Retrieve metadata
meta = byteplus_client.get_file(file_info["id"])

# Delete uploaded file
byteplus_client.delete_file(file_info["id"])
```

## Response Object

All methods return a standardized `Response` dataclass:

| Field / Property | Type | Description |
| --- | --- | --- |
| `request_id` | `str \| None` | Provider request/task identifier |
| `correlation_id` | `str \| None` | Client-generated UUID for tracing across retries and requests |
| `status` | `str \| None` | Normalized status: `queued`, `processing`, `completed`, `failed`, or `cancelled` |
| `result` | `Any` | Provider result payload (e.g. dict of URLs, image list) |
| `error` | `str \| None` | Provider error message if failed |
| `raw_request` | `Any` | Raw request body sent to the provider |
| `raw_response` | `Any` | Raw response payload received from the provider |
| `media_url` | `str \| list[str] \| None` | Extracted media URL(s) |
| `media_urls` | `list[str]` | Property returning all extracted media URLs as a list of strings |
| `bytes` | `BytesList` | Lazy property / getter downloading raw bytes for all media URLs (cached) |
| `images` | `ImagesList` | Lazy property / getter decoding downloaded bytes into PIL `Image` objects (cached) |
| `as_dict()` | `dict[str, Any]` | Serializes the response to a dictionary (omitting cached media bytes) |

## Configuration (`ClientConfig`)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `poll_timeout` | `float` | `600.0` | Maximum polling duration in seconds (10 minutes) |
| `poll_interval` | `float` | `2.0` | Seconds between polling status checks |
| `max_attempts` | `int` | `3` | Maximum HTTP retry attempts for transient failures |
| `retry_initial_delay` | `float` | `1.0` | Initial retry backoff delay in seconds |
| `retry_max_delay` | `float` | `30.0` | Maximum retry backoff delay in seconds |
| `retry_jitter` | `float` | `1.0` | Random jitter multiplier for exponential backoff |
| `cleanup_uploaded_media` | `bool` | `False` | Whether to clean up temporary uploaded media after terminal status |
| `concurrency_limit` | `int \| None` | `None` | Max concurrent HTTP requests per provider (semaphore-backed) |
| `requests_per_second` | `float \| None` | `None` | Rate limit for outgoing HTTP requests per provider |
| `media_strategy` | `str` | `"auto"` | Media strategy: `"auto"`, `"data_uri"`, or `"upload"` |
| `data_uri_max_bytes` | `int` | `10485760` | Maximum file size for data URI conversion (10 MB) |

## Workflow Inference

Workflows are inferred automatically from model-name tokens:

- `text-to-image`
- `image-to-image`
- `edit`
- `text-to-video`
- `image-to-video`
- `video-to-video`

If a model name does not contain a workflow token, the workflow defaults to `text-to-image` when no media is provided, `image-to-image` when an image is provided, and `video-to-video` when a video is provided.

When needed, pass `workflow` explicitly (aliases `t2i`, `i2i`, `t2v`, `i2v`, `v2v` are supported):

```python
response = client.submit(
    model="custom-model",
    workflow="image-to-video",  # or "i2v"
    prompt="animate water ripples",
    image="https://example.com/lake.jpg",
)
```

Input validation rules:
- `text-to-image`, `text-to-video`: rejects `image` or `video` inputs.
- `image-to-image`, `image-to-video`, `edit`: requires `image` and rejects `video`.
- `video-to-video`: requires `video` and rejects `image`.

## Media Handling

- **URLs**: Public `http://`, `https://`, and `oss://` URLs pass through directly.
- **Data URIs**: `data:...;base64,...` URIs pass through directly.
- **Local Files**:
  - **fal.ai**: Converted to base64 data URIs up to `data_uri_max_bytes` (10 MB default).
  - **KIE**: Automatically uploaded to `https://kieai.redpandaai.co/api/file-stream-upload` via multipart form upload; returned download URL is passed to the generation model.
  - **BytePlus**: Image workflows convert local images to data URIs. Video workflows require public HTTP/HTTPS URLs.
  - **PixVerse**: Image-to-video requires pre-uploaded `img_id` passed in `kwargs`.

## Credentials

Credentials can be passed as a single API key string or a list of keys for load balancing:

```python
Client(provider="fal", api_key=["key-1", "key-2"])
```

When a list is provided, a random key is chosen for each logical request and reused across retries. If `api_key` is omitted, the client looks for the provider environment variable:

- `FAL_API_KEY`
- `KIE_API_KEY`
- `PIXVERSE_API_KEY`
- `BYTEPLUS_API_KEY`

Keys are redacted and never appear in logs, exception messages, normalized responses, or statistics records.

## Webhook Endpoint

The repository includes a standalone webhook receiver server in `srv/`:

```text
POST /api/webhook
```

Configure your provider `webhook` / `callBackUrl` to point to `https://<your-host>/api/webhook`. Received media files are downloaded and saved to `media/` (or `WEBHOOK_MEDIA_DIR`).

## Error Handling

Errors raise typed exceptions from `cli.core`:

- `HttpProviderError`: Raised on non-successful HTTP responses ($\ge 400$). Includes `status_code` and formatted provider error message.
- `CapabilityError`: Raised when attempting an unsupported workflow, webhook submission, or cancellation for a provider.
- `ProviderError`: Base exception for provider failures and exhausted retries.
- `TimeoutError`: Raised when task polling exceeds `ClientConfig.poll_timeout`.

```python
from cli.core import CapabilityError, HttpProviderError, ProviderError

try:
    response = client.submit(model="...", prompt="...")
except HttpProviderError as err:
    print(f"HTTP {err.status_code}: {err}")
except CapabilityError as err:
    print(f"Unsupported operation: {err}")
except ProviderError as err:
    print(f"Provider failure: {err}")
```

## Documentation Reference

- [`docs/fal.md`](../docs%20/fal.md): fal.ai queue endpoints, webhooks, cancellation, and payloads.
- [`docs/kie.md`](../docs%20/kie.md): KIE Market task creation, automatic uploads, and model schemas.
- [`docs/pixverse.md`](../docs%20/pixverse.md): PixVerse video endpoints, trace IDs, and parameters.
- [`docs/byteplus.md`](../docs%20/byteplus.md): BytePlus ModelArk image/video generation and Files API.

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
