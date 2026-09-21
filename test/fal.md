# Tests

## fal.ai t2i submit

> python -m test.fal --model fal-ai/z-image/turbo --prompt "dragon playing football on a beach with a beautiful lady" --output /tmp/fal4.jpg

```json
15:18:48-894076 INFO     Submit: model="fal-ai/z-image/turbo" prompt="dragon playing football on a beach with a beautiful lady" image="None" video="None" workflow="None" kwargs="{}"
15:18:48-896400 INFO     Client: Client(provider=fal config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
15:18:51-935323 INFO     Response: Response(id=01a0c41e-8411-7632-af85-4b69f2534250 status=completed error=None result={'images': [{'url': 'https://v3b.fal.media/files/b/0aab5178/Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png', 'content_type': 'image/png', 'file_name': 'Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png', 'file_size': None, 'width': 1024, 'height': 768}], 'timings': {'inference': 0.5705645640846342, 'safety_checker':
                         0.009146258933469653}, 'seed': 2135818641, 'has_nsfw_concepts': [False], 'prompt': 'dragon playing football on a beach with a beautiful lady'})
15:18:51-942833 DEBUG    Response JSON: {
                           "request_id": "01a0c41e-8411-7632-af85-4b69f2534250",
                           "correlation_id": "7671b892-55e7-42f2-a400-73ac945e6500",
                           "status": "completed",
                           "result": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab5178/Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png",
                                 "content_type": "image/png",
                                 "file_name": "Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png",
                                 "file_size": null,
                                 "width": 1024,
                                 "height": 768
                               }
                             ],
                             "timings": {
                               "inference": 0.5705645640846342,
                               "safety_checker": 0.009146258933469653
                             },
                             "seed": 2135818641,
                             "has_nsfw_concepts": [
                               false
                             ],
                             "prompt": "dragon playing football on a beach with a beautiful lady"
                           },
                           "error": null,
                           "raw_request": null,
                           "raw_response": {
                             "images": [
                               {
                                 "url": "https://v3b.fal.media/files/b/0aab5178/Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png",
                                 "content_type": "image/png",
                                 "file_name": "Hdl2MBYBqjW_2I6qcP6XK_afv0xexl.png",
                                 "file_size": null,
                                 "width": 1024,
                                 "height": 768
                               }
                             ],
                             "timings": {
                               "inference": 0.5705645640846342,
                               "safety_checker": 0.009146258933469653
                             },
                             "seed": 2135818641,
                             "has_nsfw_concepts": [
                               false
                             ],
                             "prompt": "dragon playing football on a beach with a beautiful lady"
                           }
                         }
15:18:51-946668 DEBUG    Stats: [
                           {
                             "correlation_id": "7671b892-55e7-42f2-a400-73ac945e6500",
                             "operation": "submit",
                             "request_id": "01a0c41e-8411-7632-af85-4b69f2534250",
                             "started_at": "2026-09-21T13:18:48.897317+00:00",
                             "ended_at": "2026-09-21T13:18:51.935044+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 4,
                             "latency": 3.0377501689999917,
                             "error": null
                           }
                         ]
```
