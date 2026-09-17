# Tests

> python test/kie.py --model z-image --prompt "sylish arcane-style photo of a sexy young woman on a beach" --kwargs '{ "nsfw_checker": false, "aspect_ratio": "1:1"}'
> python test/kie.py --model nano-banana-2-lite --prompt "sylish anime-style photo of a young woman on a beach" --workflow i2i --image https://cdn.pixabay.com/photo/2024/04/16/21/11/ai-generated-8700789_1280.jpg --kwargs '{ "aspect_ratio": "auto"}'

```log
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

> python test/kie.py --model bytedance/seedance-2-5 --prompt "sylish anime-style photo of a young woman dancing on a beach" --kwargs '{ "aspect_ratio": "auto", "generate_audio": false, "resolution": "480p", "aspect_ratio": "adaptive", "duration": 5, "output_format": "mp4", "web_search": false, "nsfw_checker": false }'
```log

```