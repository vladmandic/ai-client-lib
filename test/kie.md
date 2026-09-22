# Test KIE

## t2i submit synchronous

> python -m test.kie --model z-image --output samples/output-kie.png --prompt "sylish arcane-style photo of a model on a beach" --kwargs '{ "nsfw_checker": false, "aspect_ratio": "16:9" }'

```log
10:58:48-519576 INFO     Submit: model="z-image" prompt="sylish arcane-style photo of a model on a beach" image="None" video="None" workflow="None" kwargs="{'nsfw_checker': False, 'aspect_ratio': '16:9'}"
10:58:48-521140 INFO     Client: Client(provider=kie config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
10:58:55-618730 INFO     Response: Response(id="cdb875af69fcf29b601e352416c466e6" status="completed" error="success" media="https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png" result="{'resultUrls': ['https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png']}")
10:58:55-619452 INFO     Media URL: https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png
10:58:56-250404 INFO     Media: items=1 bytes=[1109411] images=[<PIL.PngImagePlugin.PngImageFile image mode=RGB size=1280x720 at 0x71A59BCB87D0>] save=True
10:58:56-460469 INFO     Output: path="samples/output-kie.png"
10:58:56-465174 DEBUG    Response JSON: {
                           "request_id": "cdb875af69fcf29b601e352416c466e6",
                           "correlation_id": "563da4e9-e06c-4669-b77d-03be3b31d0b6",
                           "status": "completed",
                           "result": {
                             "resultUrls": [
                               "https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png"
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
                               "taskId": "cdb875af69fcf29b601e352416c466e6",
                               "model": "z-image",
                               "state": "success",
                               "param": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a model on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}",
                               "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png\"]}",
                               "failCode": null,
                               "failMsg": null,
                               "costTime": 4,
                               "completeTime": 1790067533916,
                               "createTime": 1790067528689,
                               "creditsConsumed": 0.8,
                               "operationType": "z-image",
                               "response": {
                                 "resultUrls": [
                                   "https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png"
                                 ]
                               },
                               "successFlag": 1,
                               "paramJson": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a model on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}"
                             }
                           },
                           "media_url": "https://tempfile.aiquickdraw.com/js/z5/54f10d3b4e84.png"
                         }
10:58:56-467652 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "563da4e9-e06c-4669-b77d-03be3b31d0b6",
                             "operation": "submit",
                             "request_id": "cdb875af69fcf29b601e352416c466e6",
                             "started_at": "2026-09-22T08:58:48.521964+00:00",
                             "ended_at": "2026-09-22T08:58:55.618689+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 7.096718771999804,
                             "error": null
                           }
                         ]
```

## i2i submit synchronous

> python -m test.kie --model seedream/5-lite-image-to-image --image samples/natgeo.jpg --output samples/output-kie-i2i.png --prompt "remove the text in top-left and brighten her skin-tone" --kwargs '{ "nsfw_checker": false }'

```log
11:16:20-507413 INFO     Submit: model="seedream/5-lite-image-to-image" prompt="remove the text in top-left and brighten her skin-tone" image="samples/natgeo.jpg" video="None" workflow="None" kwargs="{'nsfw_checker': False, 'aspect_ratio': '16:9'}"
11:16:20-509211 INFO     Client: Client(provider=kie config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
11:17:00-319622 INFO     Response: Response(id="c1fe63b2cd2df5f6b57a2d7fca1ff29b" status="completed" error="success" media="https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg" result="{'resultUrls': ['https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg']}")
11:17:00-320383 INFO     Media URL: https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg
11:17:00-782343 INFO     Media: items=1 bytes=[388588] images=[<PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=2736x1520 at 0x7E1742C7D9D0>] save=True
11:17:01-243380 INFO     Output: path="samples/output-kie-i2i.png"
11:17:01-259722 DEBUG    Response JSON: {
                           "request_id": "c1fe63b2cd2df5f6b57a2d7fca1ff29b",
                           "correlation_id": "84c0987d-8e6d-494f-a139-1b34e9e5c51a",
                           "status": "completed",
                           "result": {
                             "resultUrls": [
                               "https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg"
                             ]
                           },
                           "error": "success",
                           "raw_request": {
                             "model": "seedream/5-lite-image-to-image",
                             "input": {
                               "prompt": "remove the text in top-left and brighten her skin-tone",
                               "nsfw_checker": false,
                               "aspect_ratio": "16:9",
                               "quality": "basic",
                               "image_urls": [
                                 "https://tempfile.redpandaai.co/kieai/11657679/media/natgeo.jpg"
                               ]
                             }
                           },
                           "raw_response": {
                             "code": 200,
                             "msg": "success",
                             "data": {
                               "taskId": "c1fe63b2cd2df5f6b57a2d7fca1ff29b",
                               "model": "seedream/5-lite-image-to-image",
                               "state": "success",
                               "param": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"image_urls\\\":[\\\"https://tempfile.redpandaai.co/kieai/11657679/media/natgeo.jpg\\\"],\\\"prompt\\\":\\\"remove the text in top-left and brighten her skin-tone\\\",\\\"nsfw_checker\\\":false,\\\"quality\\\":\\\"basic\\\"}\",\"model\":\"seedream/5-lite-image-to-image\"}",
                               "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg\"]}",
                               "failCode": null,
                               "failMsg": null,
                               "costTime": 37,
                               "completeTime": 1790068620070,
                               "createTime": 1790068582661,
                               "creditsConsumed": 5.5,
                               "operationType": "seedream/5-lite-image-to-image",
                               "response": {
                                 "resultUrls": [
                                   "https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg"
                                 ]
                               },
                               "successFlag": 1,
                               "paramJson": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"16:9\\\",\\\"image_urls\\\":[\\\"https://tempfile.redpandaai.co/kieai/11657679/media/natgeo.jpg\\\"],\\\"prompt\\\":\\\"remove the text in top-left and brighten her skin-tone\\\",\\\"nsfw_checker\\\":false,\\\"quality\\\":\\\"basic\\\"}\",\"model\":\"seedream/5-lite-image-to-image\"}"
                             }
                           },
                           "media_url": "https://tempfile.aiquickdraw.com/p/c1fe63b2cd2df5f6b57a2d7fca1ff29b_1_1790068619_1207.jpg"
                         }
11:17:01-262471 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "84c0987d-8e6d-494f-a139-1b34e9e5c51a",
                             "operation": "submit",
                             "request_id": "c1fe63b2cd2df5f6b57a2d7fca1ff29b",
                             "started_at": "2026-09-22T09:16:20.510075+00:00",
                             "ended_at": "2026-09-22T09:17:00.319559+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 39.8094773770008,
                             "error": null
                           }
                         ]
```
