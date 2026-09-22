# test kie.ai

## t2i submit synchronous

> python -m test.client --provider kie --model z-image --output samples/output-kie.png --prompt "sylish arcane-style photo of a model on a beach" --kwargs '{ "nsfw_checker": false, "aspect_ratio": "16:9" }'

```log
17:24:25-006025 INFO     Submit: provider="kie" model="z-image" prompt="sylish arcane-style photo of a model on a beach" image="None" video="None" workflow="None" kwargs="{'nsfw_checker': False, 'aspect_ratio': '16:9'}"
17:24:25-007732 INFO     Client: Client(provider=kie config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
17:24:32-089928 INFO     Response: Response(id="1b6e6565b7b282e3b72f1a7eb1405f9d" status="completed" error="success" media="https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png" result="{'resultUrls': ['https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png']}")
17:24:32-091720 INFO     Media URL: https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png
17:24:32-530312 INFO     Media: items=1 bytes=[933086] images=[<PIL.PngImagePlugin.PngImageFile image mode=RGB size=1280x720 at 0x7B250F22DB80>] save=True
17:24:32-720106 INFO     Output: path="samples/output-kie.png"
17:24:32-724034 DEBUG    Response JSON: {
                           "request_id": "1b6e6565b7b282e3b72f1a7eb1405f9d",
                           "correlation_id": "ee629ac6-8c01-4a43-9e9a-d858ae2fd147",
                           "status": "completed",
                           "result": {
                             "resultUrls": [
                               "https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png"
                             ]
                           },
                           "error": "success",
                           "raw_request": {
                             "model": "z-image",
                             "input": {
                               "prompt": "sylish arcane-style photo of a model on a beach",
                               "nsfw_checker": false,
                               "aspect_ratio": "16:9"
                             }
                           },
                           "raw_response": {
                             "code": 200,
                             "msg": "success",
                             "data": {
                               "taskId": "1b6e6565b7b282e3b72f1a7eb1405f9d",
                               "model": "z-image",
                               "state": "success",
                               "param": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a model on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}",
                               "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png\"]}",
                               "failCode": null,
                               "failMsg": null,
                               "costTime": 5,
                               "completeTime": 1790090670333,
                               "createTime": 1790090665254,
                               "creditsConsumed": 0.8,
                               "operationType": "z-image",
                               "response": {
                                 "resultUrls": [
                                   "https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png"
                                 ]
                               },
                               "successFlag": 1,
                               "paramJson": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a model on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}"
                             }
                           },
                           "media_url": "https://tempfile.aiquickdraw.com/js/z5/9d189fc87c16.png"
                         }
17:24:32-726458 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "ee629ac6-8c01-4a43-9e9a-d858ae2fd147",
                             "operation": "submit",
                             "request_id": "1b6e6565b7b282e3b72f1a7eb1405f9d",
                             "started_at": "2026-09-22T15:24:25.008453+00:00",
                             "ended_at": "2026-09-22T15:24:32.089846+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 7.081390621999162,
                             "error": null
                           }
                         ]
```
