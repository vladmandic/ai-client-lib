# VidLab

The `vidilab` provider uses the [VidLab generations API](https://docs.vidlab.ai/quickstart) at `https://vidlab.ai/v1`.

## Credentials

Set `VIDILAB_API_KEY` or pass `api_key` when constructing a client. Requests use Bearer authentication. Keep the key in an environment variable or secret store, never in source code.

## Supported models and workflows

| Model | Workflows |
| --- | --- |
| `nano-banana-2` | `text-to-image` (`t2i`), `image-to-image` (`i2i`) |
| `gpt-image-2` | `text-to-image` (`t2i`), `image-to-image` (`i2i`) |
| `seedance-2.5-flash` | `text-to-video` (`t2v`), `image-to-video` (`i2v`) |
| `wan-3.0` | `text-to-video` (`t2v`), `image-to-video` (`i2v`) |
| `kling-4.0` | `text-to-video` (`t2v`), `image-to-video` (`i2v`) |

Model-specific input options are passed through as keyword arguments. For example, video generation accepts `duration=5`; see the official model pages for each model's supported fields and constraints.

## Synchronous generation

`submit` creates a generation and polls `GET /v1/generations/{id}?wait=...` until it succeeds or fails. On success, the normalized response exposes output URLs through `media_url`; `.bytes` and `.images` download those outputs.

```python
from cli import Client

with Client("vidilab") as client:
    response = client.submit(
        model="nano-banana-2",
        workflow="t2i",
        prompt="A red fox on a snowy alpine ridge at sunrise",
        resolution="0.5k",
        aspect_ratio="1:1",
        max_cost_usd=0.25,
    )
    response.images[0].save("fox.png")
```

For image-to-image or image-to-video, pass a local file or public URL as `image`. Local files are uploaded to `POST /v1/uploads` and the returned URL is sent in the generation request. Public HTTPS URLs and base64 data URLs pass through unchanged.

```python
response = client.submit(
    model="wan-3.0",
    workflow="i2v",
    prompt="Animate the scene with a slow camera push toward the horizon",
    image="samples/natgeo.jpg",
    duration=5,
    resolution="480p",
)
response.bytes[0]  # MP4 file bytes
```

VidLab accepts a `max_cost_usd` limit at the top level of the request. Pass it as a keyword argument to prevent a generation from exceeding a chosen amount.

## Asynchronous generation and webhooks

`submit_async` sends the supplied webhook URL as `webhook_url` and returns the queued `Response` immediately:

```python
response = client.submit_async(
    model="kling-4.0",
    workflow="t2v",
    prompt="A slow push-in on a perfume bottle on wet black stone",
    webhook="https://example.com/api/webhook",
    duration=5,
)
print(response.request_id, response.status)
```

VidLab webhooks contain the generation ID and status, not its outputs. The callback receiver should call `client.status(response.request_id)` to retrieve the authoritative result. Webhook callbacks are not signed by VidLab, so verify the generation by reading it with the API key before acting on the callback. `status` supports VidLab's long-poll `wait` parameter from 0 to 60 seconds.

Cancellation and video-to-video are not documented for these models and raise `CapabilityError`.

## API lifecycle

- Upload local media: `POST /v1/uploads` with raw bytes and its media type.
- Submit: `POST /v1/generations` with `{model, input, webhook_url?}`.
- Status: `GET /v1/generations/{id}?wait=...`.
- Output URLs are returned in `data.outputs`; the response adapter exposes them as `media_url`.
- Every submission sends a fresh `Idempotency-Key` unless `idempotency_key` is provided.

See the official [quickstart](https://docs.vidlab.ai/quickstart), [go-live checklist](https://docs.vidlab.ai/go-live), [image models](https://docs.vidlab.ai/models/nano-banana-2), and [video models](https://docs.vidlab.ai/models/seedance-2.5-flash) for current request schemas and limits.
