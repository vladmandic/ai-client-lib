# BytePlus ModelArk API Notes

Verified: 2026-09-07

Source: https://ai.byteplus.com/ark/region:ap-southeast-1/docs/ModelArk/1099455

Additional verified references:

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

- `submit`: image workflows call the synchronous image endpoint; video workflows create a task and poll until completion.
- `submit_async`: webhook callbacks are not documented by these references, so the adapter reports unsupported.
- `status`: query the documented video task endpoint and normalize `queued`, `running`, `succeeded`, `failed`, `cancelled`, and `expired`.
- `cancel`: delete/cancel queued video tasks through the documented DELETE endpoint. Running tasks cannot be cancelled; completed/failed records may be deleted.
- `upload_file`, `upload_url`, `get_file`, and `delete_file`: expose the verified Files API lifecycle. Uploaded files are temporary and normally retained for 7 days.

## Known gaps

- The adapter supports the documented image endpoint and Seedance-style video task lifecycle; model-specific fields remain in `kwargs`.
- Webhook submission remains unsupported.
- File IDs are not automatically inserted into Seedance generation content because the generation reference documents URL assets while the Files API examples document file IDs for Responses/Chat. Use the explicit Files API methods until that generation payload contract is verified.
- Seedance 2.5 has model-specific constraints for reference assets, duration, ratio, output format, and task type; callers must provide those through `kwargs`.
- Image URLs/base64 are documented; video inputs require public URLs or asset IDs. Local video paths are not automatically uploaded.
- Do not expose confidential or personal data in live validation; BytePlus explicitly warns that prompts and responses are processed under its privacy terms.
