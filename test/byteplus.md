# Test BytePlus

## t2i submit synchronous

> python -m test.byteplus --model seedream-5-0-lite-260128 --output samples/output-byteplus.png --prompt "sylish arcane-style photo of a model on a beach" --kwargs '{ "watermark": false, "size": "2k", "aspect_ratio": "16:9" }'

```json
11:00:45-654769 INFO     Submit: model="seedream-5-0-lite-260128" prompt="sylish arcane-style photo of a dragon on a beach" image="None" video="None" workflow="None" kwargs="{'watermark': False, 'size': '2k', 'aspect_ratio': '16:9'}"
11:00:45-656431 INFO     Client: Client(provider=byteplus config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
11:01:13-170790 INFO     Response: Response(id="e809a75d-70d2-44a5-8bdd-9f7492fa2800" status="completed" error="None"
                         media="https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-SignedHeaders=host" result="[{'url':
                         'https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T090113Z&X-Tos-Expires=86400&X-Tos-SignedHeaders=host'', 'size': '2848x1600'}]")
11:01:13-172093 INFO     Media URL: https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T090113Z&X-Tos-Expires=86400&X-Tos-Signature=c74c325da6c40da0a75282874b179d929869f70daeb93acf6914f20b952fad74&X-Tos-SignedHeaders=host
11:01:14-833491 INFO     Media: items=1 bytes=[413941] images=[<PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=2848x1600 at 0x7182BEF220F0>] save=True
11:01:15-357267 INFO     Output: path="samples/output-byteplus.png"
11:01:15-372637 DEBUG    Response JSON: {
                           "request_id": "e809a75d-70d2-44a5-8bdd-9f7492fa2800",
                           "correlation_id": "e809a75d-70d2-44a5-8bdd-9f7492fa2800",
                           "status": "completed",
                           "result": [
                             {
                               "url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T090113Z&X-Tos-Expires=86400&X-Tos-SignedHeaders=host",
                               "size": "2848x1600"
                             }
                           ],
                           "error": null,
                           "raw_request": {
                             "model": "seedream-5-0-lite-260128",
                             "prompt": "sylish arcane-style photo of a dragon on a beach",
                             "watermark": false,
                             "size": "2k",
                             "aspect_ratio": "16:9"
                           },
                           "raw_response": {
                             "model": "seedream-5-0-260128",
                             "created": 1790067673,
                             "data": [
                               {
                                 "url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T090113Z&X-Tos-Expires=86400q&X-Tos-SignedHeaders=host",
                                 "size": "2848x1600"
                               }
                             ],
                             "usage": {
                               "generated_images": 1,
                               "output_tokens": 17800,
                               "total_tokens": 17800
                             }
                           },
                           "media_url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/0217900676461845b7c5d80188542749d9bf0e4ecbfb37fcd7110_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T090113Z&X-Tos-Expires=86400&X-Tos-SignedHeaders=host"
                         }
11:01:15-375116 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "e809a75d-70d2-44a5-8bdd-9f7492fa2800",
                             "operation": "submit",
                             "request_id": "e809a75d-70d2-44a5-8bdd-9f7492fa2800",
                             "started_at": "2026-09-22T09:00:45.657172+00:00",
                             "ended_at": "2026-09-22T09:01:13.170739+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 27.513570996999988,
                             "error": null
                           }
                         ]
```                         

## t2i submit

> python -m test.byteplus --model seedream-5-0-lite-260128 --image samples/cartoon.jpg --output samples/output-byteplus-i2i.png --prompt "change the image style to anime" --kwargs '{ "watermark": false }'

```json
11:31:09-843286 INFO     Submit: model="seedream-5-0-lite-260128" prompt="change the image style to anime" image="samples/cartoon.jpg" video="None" workflow="None" kwargs="{'watermark': False}"
11:31:09-844905 INFO     Client: Client(provider=byteplus config=ClientConfig(poll_timeout=600.0 poll_interval=2.0 max_attempts=3 retry_initial_delay=1.0 retry_max_delay=30.0 retry_jitter=1.0 cleanup_uploaded_media=False concurrency_limit=None requests_per_second=None media_strategy="auto" data_uri_max_bytes=10485760))
11:31:40-546496 INFO     Response: Response(id="8527eddf-9ea0-45b4-a2f4-fca2445d5260" status="completed" error="None"
                         media="https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Date=20260922T093140Z&X-Tos-Expires=86400&X-Tos-SignedHeaders=host" result="[{'url':
                         'https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Expires=86400&X-Tos-SignedHeaders=host', 'size': '2048x2048'}]")
11:31:40-549557 INFO     Media URL: https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&&X-Tos-Expires=86400&X-Tos-SignedHeaders=host
11:31:42-395962 INFO     Media: items=1 bytes=[993144] images=[<PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=2048x2048 at 0x70613BB725A0>] save=True
11:31:42-961685 INFO     Output: path="samples/output-byteplus-i2i.png"
11:31:42-979430 DEBUG    Response JSON: {
                           "request_id": "8527eddf-9ea0-45b4-a2f4-fca2445d5260",
                           "correlation_id": "8527eddf-9ea0-45b4-a2f4-fca2445d5260",
                           "status": "completed",
                           "result": [
                             {
                               "url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Expires=86400&X-Tos-SignedHeaders=host",
                               "size": "2048x2048"
                             }
                           ],
                           "error": null,
                           "raw_request": {
                             "model": "seedream-5-0-lite-260128",
                             "prompt": "change the image style to anime",
                             "watermark": false,
                             "image":
                         "data:image/jpeg;base64,..."
                           },
                           "raw_response": {
                             "model": "seedream-5-0-260128",
                             "created": 1790069500,
                             "data": [
                               {
                                 "url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Expires=86400&X-Tos-SignedHeaders=host",
                                 "size": "2048x2048"
                               }
                             ],
                             "usage": {
                               "generated_images": 1,
                               "output_tokens": 16384,
                               "total_tokens": 16384
                             }
                           },
                           "media_url": "https://ark-acg-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-5-0/02179006947039261de39c93fac111732577779cd317989b78bbb_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Expires=86400&X-Tos-SignedHeaders=host"
                         }
11:31:43-028158 DEBUG    Stats JSON: [
                           {
                             "correlation_id": "8527eddf-9ea0-45b4-a2f4-fca2445d5260",
                             "operation": "submit",
                             "request_id": "8527eddf-9ea0-45b4-a2f4-fca2445d5260",
                             "started_at": "2026-09-22T09:31:09.845632+00:00",
                             "ended_at": "2026-09-22T09:31:40.546300+00:00",
                             "status": "completed",
                             "http_status": 200,
                             "attempts": 1,
                             "latency": 30.7007336810002,
                             "error": null
                           }
                         ]
```
