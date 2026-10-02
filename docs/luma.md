# Luma Agents

The `luma` provider uses the [Luma Agents API](https://docs.agents.lumalabs.ai/) at `https://agents.lumalabs.ai/v1`.

## Credentials

Set `LUMA_API_KEY` or pass `api_key` when constructing a client. Requests use Bearer authentication.

## Supported workflows

| Workflow | Luma request type | Input mapping |
| --- | --- | --- |
| `text-to-image` (`t2i`) | `image` | Prompt and image-generation options |
| `image-to-image` / `edit` (`i2i`) | `image_edit` | `image` becomes `source` |
| `text-to-video` (`t2v`) | `video` | Prompt and video options |
| `image-to-video` (`i2v`) | `video` | `image` becomes `video.start_frame` |

The default image model is `uni-1` and the video model is `ray-3.2`; pass the relevant model explicitly with `model`. Standard `submit` waits for completion by polling the generation endpoint. Luma generation responses include expiring output URLs, which the client exposes as `media_url` and downloads when accessing `bytes` or `images`.

Public image URLs are passed through. Local images are converted to base64 data and sent inline, subject to the shared `data_uri_max_bytes` limit. The Luma API accepts image data up to 50 MB, but the shared client defaults to a 10 MB local-media limit; raise `ClientConfig.data_uri_max_bytes` when needed.

```python
from cli import Client, ClientConfig

with Client(
    "luma",
    config=ClientConfig(data_uri_max_bytes=50 * 1024 * 1024),
) as client:
    response = client.submit(
        model="uni-1",
        prompt="A quiet alpine lake at sunrise",
        workflow="t2i",
        aspect_ratio="16:9",
    )
    response.images[0].save("lake.png")
```

For image-to-video, pass an image and `workflow="i2v"`; video parameters such as resolution and duration can be passed in a `video` dictionary through `kwargs`:

```python
response = client.submit(
    model="ray-3.2",
    prompt="The trees sway gently as the camera moves forward",
    image="samples/natgeo.jpg",
    workflow="i2v",
    aspect_ratio="16:9",
    video={"resolution": "720p", "duration": "5s"},
)
```

Webhook submission, cancellation, and video-to-video are not implemented because they are not documented by the referenced generation endpoints.

## API lifecycle

- `POST /v1/generations` submits image or video generation.
- `GET /v1/generations/{id}` retrieves status and completed output.
- States `queued`, `processing`, `completed`, and `failed` are normalized to the shared response status values.

See the official [image generation](https://docs.agents.lumalabs.ai/guides/images/generation/), [image editing](https://docs.agents.lumalabs.ai/guides/images/editing/), and [video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/) guides for model and option constraints.