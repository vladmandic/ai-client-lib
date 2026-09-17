# Tests

## kie t2i submit

> python test/kie.py --model z-image --prompt "sylish arcane-style photo of a sexy young woman on a beach" --kwargs '{ "nsfw_checker": false, "aspect_ratio": "1:1"}'
```json
11:22:53-158735 INFO     Submit: model="z-image" prompt="sylish arcane-style photo of a sexy young woman on a beach" image="None" video="None" workflow="None" kwargs="{'nsfw_checker': False, 'aspect_ratio': '1:1'}"
11:22:53-161330 INFO     Client: Client(provider=kie config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
11:23:00-221974 INFO     Response: Response(id=152e948a28b9f2bb6525e0ae9a01ecd1 status=completed error=success result={'resultUrls': ['https://tempfile.aiquickdraw.com/js/z5/e2c45ea55350.png']})
11:23:00-222836 DEBUG    Request JSON: {
                           "model": "z-image",
                           "input": {
                             "prompt": "sylish arcane-style photo of a sexy young woman on a beach",
                             "nsfw_checker": false,
                             "aspect_ratio": "1:1"
                           }
                         }
11:23:00-223650 DEBUG    Response JSON: {
                           "code": 200,
                           "msg": "success",
                           "data": {
                             "taskId": "152e948a28b9f2bb6525e0ae9a01ecd1",
                             "model": "z-image",
                             "state": "success",
                             "param": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"1:1\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a sexy young woman on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}",
                             "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/js/z5/e2c45ea55350.png\"]}",
                             "failCode": null,
                             "failMsg": null,
                             "costTime": 6,
                             "completeTime": 1789644179089,
                             "createTime": 1789644173377,
                             "creditsConsumed": 0.8,
                             "operationType": "z-image",
                             "response": {
                               "resultUrls": [
                                 "https://tempfile.aiquickdraw.com/js/z5/e2c45ea55350.png"
                               ]
                             },
                             "successFlag": 1,
                             "paramJson": "{\"input\":\"{\\\"aspect_ratio\\\":\\\"1:1\\\",\\\"prompt\\\":\\\"sylish arcane-style photo of a sexy young woman on a beach\\\",\\\"nsfw_checker\\\":false}\",\"model\":\"z-image\"}"
                           }
                         }
11:23:00-225305 DEBUG    Stats: [
                           {
                             "correlation_id": "732a2aaa-b75a-42e7-8178-04eb4a68beb8",
                             "operation": "submit",
                             "request_id": "152e948a28b9f2bb6525e0ae9a01ecd1",
                             "started_at": "2026-09-17T11:22:53.162145+00:00",
                             "ended_at": "2026-09-17T11:23:00.221934+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 5,
                             "latency": 7.05978224799037,
                             "error": null
                           }
                         ]
```

## kie t2i webhook

> python test/kie.py --model z-image --prompt "sylish arcane-style photo of a sexy young woman on a beach" --kwargs '{ "nsfw_checker": false, "aspect_ratio": "1:1"}' --webhook "https://6lfizm6y1y8w72-8080.proxy.runpod.net/api/webhook"
```json
11:20:41-577185 INFO     Webhook(headers={'host': '100.65.32.184:60280', 'user-agent': 'okhttp/3.14.9', 'content-length': '630', 'accept-encoding': 'gzip, br', 'cdn-loop': 'cloudflare; loops=1', 'cf-connecting-ip': '43.110.34.67', 'cf-ipcountry': 'US', 'cf-ray': 'a3c7b9173a14eb31-SJC', 'cf-visitor': '{"scheme":"https"}', 'content-type': 'application/json; charset=utf-8', 'x-forwarded-for': '43.110.34.67,
                         162.158.167.212', 'x-forwarded-host': '6lfizm6y1y8w72-8080.proxy.runpod.net', 'x-forwarded-proto': 'https'} payload={'code': 200, 'data': {'completeTime': 1789644040779, 'costTime': 5, 'createTime': 1789644035000, 'creditsConsumed': 0.8, 'model': 'z-image', 'param': '{"input":"{\\"aspect_ratio\\":\\"1:1\\",\\"prompt\\":\\"sylish arcane-style photo of a sexy young woman on a
                         beach\\",\\"nsfw_checker\\":false}","callBackUrl":"https://6lfizm6y1y8w72-8080.proxy.runpod.net/api/webhook","model":"z-image"}', 'resultJson': '{"resultUrls":["https://tempfile.aiquickdraw.com/js/z5/e0d4aad91621.png"]}', 'state': 'success', 'taskId': '1134f5cf800a6be035c8794c90d53760', 'updateTime': 1789644035000}, 'msg': 'Playground task completed successfully.'})
11:20:41-578921 DEBUG    API(code=202 protocol=http/1.1 method=POST endpoint=/api/webhook client=100.64.1.101 duration=0.0027)
```

## kie i2i submit

> python test/kie.py --model nano-banana-2-lite --prompt "sylish anime-style photo of a young woman on a beach" --workflow i2i --image https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg --kwargs '{ "aspect_ratio": "auto"}'
```json
11:23:04-522389 INFO     Submit: model="nano-banana-2-lite" prompt="sylish anime-style photo of a young woman on a beach" image="https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg" video="None" workflow="i2i" kwargs="{'aspect_ratio': 'auto'}"
11:23:20-394019 INFO     Response: Response(id=f3f20495db5f97c1e2ad7553da4bdfa8 status=completed error=success result={'resultUrls': ['https://tempfile.aiquickdraw.com/vnp/f3f20495db5f97c1e2ad7553da4bdfa8_0_1789636997.jpeg']})
11:23:20-396744 DEBUG    Request JSON: {
                           "model": "nano-banana-2-lite",
                           "input": {
                             "prompt": "sylish anime-style photo of a young woman on a beach",
                             "aspect_ratio": "auto",
                             "image_input": [
                               "https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg"
                             ]
                           }
                         }
11:23:20-398650 DEBUG    Response JSON: {
                           "code": 200,
                           "msg": "success",
                           "data": {
                             "taskId": "f3f20495db5f97c1e2ad7553da4bdfa8",
                             "model": "nano-banana-2-lite",
                             "state": "success",
                             "param": "{\"input\":\"{\\\"image_input\\\":[\\\"https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg\\\"],\\\"aspect_ratio\\\":\\\"auto\\\",\\\"prompt\\\":\\\"sylish anime-style photo of a young woman on a beach\\\"}\",\"model\":\"nano-banana-2-lite\"}",
                             "resultJson": "{\"resultUrls\":[\"https://tempfile.aiquickdraw.com/vnp/f3f20495db5f97c1e2ad7553da4bdfa8_0_1789636997.jpeg\"]}",
                             "failCode": null,
                             "failMsg": null,
                             "costTime": 14,
                             "completeTime": 1789636999273,
                             "createTime": 1789636984839,
                             "creditsConsumed": 4.0,
                             "operationType": "nano-banana-2-lite",
                             "response": {
                               "resultUrls": [
                                 "https://tempfile.aiquickdraw.com/vnp/f3f20495db5f97c1e2ad7553da4bdfa8_0_1789636997.jpeg"
                               ]
                             },
                             "successFlag": 1,
                             "paramJson": "{\"input\":\"{\\\"image_input\\\":[\\\"https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg\\\"],\\\"aspect_ratio\\\":\\\"auto\\\",\\\"prompt\\\":\\\"sylish anime-style photo of a young woman on a beach\\\"}\",\"model\":\"nano-banana-2-lite\"}"
                           }
                         }
```

## kie t2v submit

> python test/kie.py --model bytedance/seedance-2-5 --prompt "sylish anime-style photo of a young woman dancing on a beach" --kwargs '{ "aspect_ratio": "auto", "generate_audio": false, "resolution": "480p", "aspect_ratio": "adaptive", "duration": 5, "output_format": "mp4", "web_search": false, "nsfw_checker": false }'

## kie i2v webhook

> python test/kie.py --model bytedance/seedance-2-5 --prompt "sylish anime-style photo of a young woman dancing on a beach" --kwargs '{ "aspect_ratio": "auto", "generate_audio": false, "resolution": "480p", "aspect_ratio": "adaptive", "duration": 5, "output_format": "mp4", "web_search": false, "nsfw_checker": false }'
