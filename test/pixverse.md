# test pixverse

## t2v submit synchronous

> python -m test.pixverse --model c1 --prompt "android dancing on the mooon" --kwargs '{"aspect_ratio": "16:9", "duration": 5, "quality": "720p"}'

```json
17:16:39-425722 INFO     Submit: model="c1" prompt="android dancing on the mooon" image="None" video="None" workflow="None" kwargs="{'aspect_ratio': '16:9', 'duration': 5, 'quality': '720p'}"
17:16:39-427317 INFO     Client: Client(provider=pixverse config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
17:17:19-788027 INFO     Response: Response(id="425918148159561" status="completed" error="None" media="https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4" result="{'id': 425918148159561, 'prompt': 'android dancing on the mooon', 'negative_prompt': '', 'resolution_ratio': 0, 'url': 'https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4', 'path':
                         'pixverse/mp4/media/web/ori/7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4', 'size': 5, 'seed': 1356037533, 'status': 1, 'style': '', 'create_time': '2026-09-22T15:16:40Z', 'modify_time': '2026-09-22T15:17:18Z', 'outputWidth': 1280, 'outputHeight': 720, 'quality': '720p', 'duration': 5, 'aspect_ratio': '16:9', 'has_audio': False, 'credits': 50, 'customer_paths': {'ext_info': None, 'agent_info': None, 'cameo_id_list': None, 'duration_type': '',
                         'thinking_type': 'enabled', 'caption_switch': False, 'fusion_id_list': None, 'model_evaluator': '', 'use_api_gen_image': False}}")
17:17:19-791298 INFO     Media URL: https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4
17:17:20-848814 INFO     Media: items=1 bytes=[2249345] images=[] save=False
17:17:20-849500 DEBUG    Response JSON: {
                           "request_id": "425918148159561",
                           "correlation_id": "445c1593-6ddf-462b-8ba7-082b4d4acfd0",
                           "status": "completed",
                           "result": {
                             "id": 425918148159561,
                             "prompt": "android dancing on the mooon",
                             "negative_prompt": "",
                             "resolution_ratio": 0,
                             "url": "https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4",
                             "path": "pixverse/mp4/media/web/ori/7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4",
                             "size": 5,
                             "seed": 1356037533,
                             "status": 1,
                             "style": "",
                             "create_time": "2026-09-22T15:16:40Z",
                             "modify_time": "2026-09-22T15:17:18Z",
                             "outputWidth": 1280,
                             "outputHeight": 720,
                             "quality": "720p",
                             "duration": 5,
                             "aspect_ratio": "16:9",
                             "has_audio": false,
                             "credits": 50,
                             "customer_paths": {
                               "ext_info": null,
                               "agent_info": null,
                               "cameo_id_list": null,
                               "duration_type": "",
                               "thinking_type": "enabled",
                               "caption_switch": false,
                               "fusion_id_list": null,
                               "model_evaluator": "",
                               "use_api_gen_image": false
                             }
                           },
                           "error": null,
                           "raw_request": {
                             "model": "c1",
                             "prompt": "android dancing on the mooon",
                             "aspect_ratio": "16:9",
                             "duration": 5,
                             "quality": "720p"
                           },
                           "raw_response": {
                             "ErrCode": 0,
                             "ErrMsg": "Success",
                             "Resp": {
                               "id": 425918148159561,
                               "prompt": "android dancing on the mooon",
                               "negative_prompt": "",
                               "resolution_ratio": 0,
                               "url": "https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4",
                               "path": "pixverse/mp4/media/web/ori/7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4",
                               "size": 5,
                               "seed": 1356037533,
                               "status": 1,
                               "style": "",
                               "create_time": "2026-09-22T15:16:40Z",
                               "modify_time": "2026-09-22T15:17:18Z",
                               "outputWidth": 1280,
                               "outputHeight": 720,
                               "quality": "720p",
                               "duration": 5,
                               "aspect_ratio": "16:9",
                               "has_audio": false,
                               "credits": 50,
                               "customer_paths": {
                                 "ext_info": null,
                                 "agent_info": null,
                                 "cameo_id_list": null,
                                 "duration_type": "",
                                 "thinking_type": "enabled",
                                 "caption_switch": false,
                                 "fusion_id_list": null,
                                 "model_evaluator": "",
                                 "use_api_gen_image": false
                               }
                             }
                           },
                           "media_url": "https://media.pixverse.ai/pixverse%2Fmp4%2Fmedia%2Fweb%2Fori%2F7fd23d83-fd8b-4a7f-98c7-8b5751b761ff_seed1356037533.mp4"
                         }
17:17:20-853387 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "445c1593-6ddf-462b-8ba7-082b4d4acfd0",
                             "operation": "submit",
                             "request_id": "425918148159561",
                             "started_at": "2026-09-22T15:16:39.428084+00:00",
                             "ended_at": "2026-09-22T15:17:19.787803+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 40.359728027999154,
                             "error": null
                           }
                         ]
```
