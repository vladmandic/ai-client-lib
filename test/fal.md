# test fal.ai

## t2i submit synchronous

> python -m test.fal --model fal-ai/z-image/turbo --output samples/output-fal.png --prompt "sylish arcane-style photo of a model on a beach" --kwargs '{ "enable_safety_checker ": false, "image_size": "portrait_16_9" }'

```json
10:51:10-137975 INFO     Submit: model="fal-ai/z-image/turbo" prompt="sylish arcane-style photo of a model on a beach" image="None" video="None" workflow="None" kwargs="{'enable_safety_checker ': False, 'image_size': 'portrait_16_9'}"
10:51:10-139764 INFO     Client: Client(provider=fal config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
10:51:13-106300 INFO     Response: Response(id="01a0c84f-d628-7121-b7f3-bf6c4c6a0521" status="completed" error="None" media="https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png" result="{'images': [{'url': 'https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png', 'content_type': 'image/png', 'file_name': '0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png', 'file_size': None, 'width': 576, 'height': 1024}], 'timings': {'inference': 0.7485269579919986,
                         'safety_checker': 0.019542765017831698}, 'seed': 1572146982, 'has_nsfw_concepts': [False], 'prompt': 'sylish arcane-style photo of a model on a beach'}")
10:51:13-110398 INFO     Media URL: https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png
10:51:14-425279 INFO     Media: items=1 bytes=[815328] images=[<PIL.PngImagePlugin.PngImageFile image mode=RGB size=576x1024 at 0x753D8DAF3380>] save=True
10:51:14-570300 INFO     Output: path="samples/output-fal.png"
10:51:14-573658 DEBUG    Response JSON: {
                           "request_id": "01a0c84f-d628-7121-b7f3-bf6c4c6a0521",
                           "correlation_id": "70075c9c-ae2e-4d4e-af6c-281117943ef9",
                           "status": "completed",
                           "result": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png",
                                 "content_type": "image/png",
                                 "file_name": "0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png",
                                 "file_size": null,
                                 "width": 576,
                                 "height": 1024
                               }
                             ],
                             "timings": {
                               "inference": 0.7485269579919986,
                               "safety_checker": 0.019542765017831698
                             },
                             "seed": 1572146982,
                             "has_nsfw_concepts": [
                               false
                             ],
                             "prompt": "sylish arcane-style photo of a model on a beach"
                           },
                           "error": null,
                           "raw_request": {
                             "enable_safety_checker ": false,
                             "image_size": "portrait_16_9",
                             "prompt": "sylish arcane-style photo of a model on a beach"
                           },
                           "raw_response": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png",
                                 "content_type": "image/png",
                                 "file_name": "0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png",
                                 "file_size": null,
                                 "width": 576,
                                 "height": 1024
                               }
                             ],
                             "timings": {
                               "inference": 0.7485269579919986,
                               "safety_checker": 0.019542765017831698
                             },
                             "seed": 1572146982,
                             "has_nsfw_concepts": [
                               false
                             ],
                             "prompt": "sylish arcane-style photo of a model on a beach"
                           },
                           "media_url": "https://v3b.fal.media/files/b/0aab6cf3/0Oo-2d6DzGdPHaefOfrS3_2qww6PcO.png"
                         }
10:51:14-576618 DEBUG    Stats: [
                           {
                             "correlation_id": "70075c9c-ae2e-4d4e-af6c-281117943ef9",
                             "operation": "submit",
                             "request_id": "01a0c84f-d628-7121-b7f3-bf6c4c6a0521",
                             "started_at": "2026-09-22T08:51:10.140480+00:00",
                             "ended_at": "2026-09-22T08:51:13.105757+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 2.9653145239999503,
                             "error": null
                           }
                         ]
```

## i2i submit synchronous

> python -m test.fal --model google/nano-banana-lite/edit --image samples/natgeo.jpg --output samples/output-fal-i2i.png --prompt "remove the text in top-left and brighten her skin-tone" --kwargs '{ "safety_tolerance ": 6 }'

```json
11:26:07-994192 INFO     Submit: model="google/nano-banana-lite/edit" prompt="remove the text in top-left and brighten her skin-tone" image="samples/natgeo.jpg" video="None" workflow="None" kwargs="{'safety_tolerance ': 6}"
11:26:07-995987 INFO     Client: Client(provider=fal config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
11:26:26-372505 INFO     Response: Response(id="01a0c86f-dae3-7e93-bed5-68dfdeed742a" status="completed" error="None" media="https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png" result="{'images': [{'url': 'https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png', 'content_type': 'image/png', 'file_name': 'J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png', 'file_size': None, 'width': 1024, 'height': 1024}], 'description': ''}")
11:26:26-373380 INFO     Media URL: https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png
11:26:27-487971 INFO     Media: items=1 bytes=[1157969] images=[<PIL.PngImagePlugin.PngImageFile image mode=RGB size=1024x1024 at 0x7493D301C680>] save=True
11:26:27-663110 INFO     Output: path="samples/output-fal-i2i.png"
11:26:27-668594 DEBUG    Response JSON: {
                           "request_id": "01a0c86f-dae3-7e93-bed5-68dfdeed742a",
                           "correlation_id": "766f3101-5514-4bde-bbe2-3108b7499197",
                           "status": "completed",
                           "result": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png",
                                 "content_type": "image/png",
                                 "file_name": "J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png",
                                 "file_size": null,
                                 "width": 1024,
                                 "height": 1024
                               }
                             ],
                             "description": ""
                           },
                           "error": null,
                           "raw_request": {
                             "safety_tolerance ": 6,
                             "prompt": "remove the text in top-left and brighten her skin-tone",
                             "image_urls": [
                               "data:image/jpeg;base64,..."
                             ]
                           },
                           "raw_response": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png",
                                 "content_type": "image/png",
                                 "file_name": "J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png",
                                 "file_size": null,
                                 "width": 1024,
                                 "height": 1024
                               }
                             ],
                             "description": ""
                           },
                           "media_url": "https://v3b.fal.media/files/b/0aab6dc6/J9xi5Y5x3fvOqcdmsHU46_ZdRNeACx.png"
                         }
11:26:27-722910 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "766f3101-5514-4bde-bbe2-3108b7499197",
                             "operation": "submit",
                             "request_id": "01a0c86f-dae3-7e93-bed5-68dfdeed742a",
                             "started_at": "2026-09-22T09:26:07.996853+00:00",
                             "ended_at": "2026-09-22T09:26:26.372437+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 18.37559207599952,
                             "error": null
                           }
```
