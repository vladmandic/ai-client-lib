# BytePlus ModelArk API Notes

Verified: 2026-09-07

Source: https://ai.byteplus.com/ark/region:ap-southeast-1/docs/ModelArk/1099455

Additional verified references:

- [Video generation tutorial](https://docs.byteplus.com/en/docs/ModelArk/2298881)
- [Image generation tutorial](https://docs.byteplus.com/en/docs/ModelArk/1824121)
- [Dreamina Seedance 2.5 tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688)
- [Image generation API](https://docs.byteplus.com/en/docs/ModelArk/1541523)
- [Create video generation task](https://docs.byteplus.com/en/docs/ModelArk/1520757)
- [Retrieve video generation task](https://docs.byteplus.com/en/docs/ModelArk/1521309)
- [Cancel or delete video generation task](https://docs.byteplus.com/en/docs/ModelArk/1521720)

## API shape

- The documented ModelArk base URL for `ap-southeast-1` is `https://ark.ap-southeast.bytepluses.com/api/v3`.
- The overview shows API-key authentication through the Ark client and model requests using a model name and input.
- The platform exposes image-generation and video-generation model capabilities, but model schemas are endpoint-specific.
- The overview also identifies a File API for uploading and preprocessing images, videos, and PDFs.
- Region availability matters. The overview states that all listed models are supported in `ap-southeast-1`; some models are also supported in `eu-west-1`.
- Image generation endpoint: `POST /images/generations`.
- Video task creation endpoint: `POST /contents/generations/tasks`.
- Video task retrieval endpoint: `GET /contents/generations/tasks/{id}`.
- Video cancellation/deletion endpoint: `DELETE /contents/generations/tasks/{id}`.
- Files upload endpoint: `POST /files`.
- Files retrieve endpoint: `GET /files/{file_id}`.
- Files delete endpoint: `DELETE /files/{file_id}`.
- Authentication uses `Authorization: Bearer <ARK_API_KEY>`.

## Media and workflows

- Image generation from text and images is listed as a platform capability.
- Video generation is listed as a platform capability, including Dreamina Seedance models.
- File input supports uploaded images and videos, but the exact upload endpoint, returned file identifier, and expiration/deletion semantics require the File API documentation.
- The overview does not establish one generic payload for text-to-image, image-to-image, text-to-video, image-to-video, or video-to-video.
- Image generation accepts `prompt`, an optional `image` string or list, `size`, `output_format`, `response_format`, and model-specific options.
- Seedance 2.5 video requests use a `content` list containing text and optional image/video/audio URL assets with roles such as `first_frame`, `last_frame`, and `reference_video`.

## Implementation mapping

- `submit`: image workflows (`text-to-image`, `image-to-image`, `edit`) call the synchronous image endpoint (`POST /images/generations`); video workflows (`text-to-video`, `image-to-video`, `video-to-video`) create a generation task (`POST /contents/generations/tasks`) and poll `GET /contents/generations/tasks/{id}` until completion.
- `submit_async`: video workflows create a task with `callback_url` set to the caller's webhook URL and return the queued response immediately; image workflows raise `CapabilityError` because image generation is synchronous.
- `status`: query `GET /contents/generations/tasks/{id}` and normalize `queued`, `running` -> `processing`, `succeeded` -> `completed`, `failed`/`expired` -> `failed`, and `cancelled`.
- `cancel`: cancel/delete video tasks through `DELETE /contents/generations/tasks/{id}`.
- Files API methods: `upload_file(path, ...)`, `upload_url(url, ...)`, `get_file(file_id)`, and `delete_file(file_id)` expose the ModelArk Files API lifecycle.
- Media extraction: automatically extracts media URLs from `content` or `data` response fields, enabling lazy `.bytes` download and `.images` PIL conversion on the `Response` object.
- Base URL: supports overriding the default API base URL via the `base_url` constructor parameter.

## Known gaps

- Webhook submission is supported for video generation tasks via `callback_url`; image generation is synchronous and does not accept webhooks.
- Image workflows accept public URLs and local images (converted to data URIs); video workflows require public HTTP/HTTPS URLs.
- File IDs from the Files API are not automatically substituted into generation payloads; use the explicit Files API methods when needed.
- Seedance 2.5 has model-specific constraints for reference assets, duration, ratio, output format, and task type; callers pass these through `kwargs`.
- BytePlus ModelArk content safety checks can be strict and may reject prompts or generated outputs.
