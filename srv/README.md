# Server

HTTP server that can be used for testing:
- Provides webhook endpoint: `/api/webhook`
- Provides media endpoint: `/api/samples`

> python -m srv.server

```log
16:50:59-061050 INFO     App(name="Echonos.AI Webhook Test Server")
16:50:59-294895 DEBUG    Swagger(schema=/openapi.json url=http://localhost:8080/swagger docs=http://localhost:8080/docs redoc=http://localhost:8080/redoc)
16:50:59-296277 DEBUG    Middleware(['GZipMiddleware', 'BaseHTTPMiddleware'])
16:50:59-297141 DEBUG    Uvicorn(start=True, secure=False port=8080)
16:50:59-297631 DEBUG    Uvicorn({'app': <fastapi.applications.FastAPI object at 0x7af2b4ee6630>, 'host': '0.0.0.0', 'port': 8080, 'uds': None, 'fd': None, 'loop': 'auto', 'http': 'auto', 'http2': False, 'ws': 'auto', 'ws_max_size': 16777216, 'ws_max_queue': 32, 'ws_ping_interval': 20.0, 'ws_ping_timeout': 20.0, 'ws_per_message_deflate': True, 'lifespan': 'auto', 'log_config': {'version': 1, 'disable_existing_loggers': False, 'formatters': {'default': {'()':
                         'uvicorn.logging.DefaultFormatter', 'fmt': '%(levelprefix)s %(message)s', 'use_colors': None}, 'access': {'()': 'uvicorn.logging.AccessFormatter', 'fmt': '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'}}, 'handlers': {'default': {'formatter': 'default', 'class': 'logging.StreamHandler', 'stream': 'ext://sys.stderr'}, 'access': {'formatter': 'access', 'class': 'logging.StreamHandler', 'stream': 'ext://sys.stdout'}}, 'loggers':
                         {'uvicorn': {'handlers': ['default'], 'level': 'INFO', 'propagate': False}, 'uvicorn.error': {'level': 'INFO'}, 'uvicorn.access': {'handlers': ['access'], 'level': 'INFO', 'propagate': False}}}, 'log_level': 30, 'access_log': True, 'use_colors': None, 'interface': 'auto', 'reload': True, 'reload_delay': 0.25, 'workers': 1, 'proxy_headers': True, 'server_header': True, 'date_header': True, 'root_path': '', 'limit_concurrency': None, 'limit_max_requests':
                         None, 'limit_max_requests_jitter': 0, 'backlog': 2048, 'timeout_keep_alive': 5, 'timeout_notify': 30, 'timeout_graceful_shutdown': None, 'timeout_worker_healthcheck': 5, 'callback_notify': None, 'ssl_keyfile': None, 'ssl_certfile': None, 'ssl_keyfile_password': None, 'ssl_version': <_SSLMethod.PROTOCOL_TLS_SERVER: 17>, 'ssl_cert_reqs': <VerifyMode.CERT_NONE: 0>, 'ssl_ca_certs': None, 'ssl_ciphers': None, 'ssl_context_factory': None, 'headers': [],
                         'encoded_headers': [], 'factory': False, 'h11_max_incomplete_event_size': None, 'reset_contextvars': False, 'loaded': False, 'reload_dirs': [], 'reload_dirs_excludes': [], 'reload_includes': [], 'reload_excludes': [], 'forwarded_allow_ips': '127.0.0.1,::1'})
16:50:59-300245 DEBUG    Uvicorn(active=False port=8080 requests=0 connections=0 uptime=0.01)
16:50:59-339214 DEBUG    Route(name=openapi path=/openapi.json method={'HEAD', 'GET'})
16:50:59-340408 DEBUG    Route(name=swagger_ui_html path=/docs method={'HEAD', 'GET'})
16:50:59-340991 DEBUG    Route(name=swagger_ui_redirect path=/docs/oauth2-redirect method={'HEAD', 'GET'})
16:50:59-341788 DEBUG    Route(name=redoc_html path=/redoc method={'HEAD', 'GET'})
16:50:59-342263 DEBUG    APIRoute(name=docs path=/swagger method={'GET'})
16:50:59-342839 DEBUG    APIRoute(name=get_root path=/ method={'GET'})
16:50:59-343316 DEBUG    APIRoute(name=get_ping path=/api/ping method={'GET'})
16:50:59-343827 DEBUG    APIRoute(name=list_samples path=/api/samples method={'GET'})
16:50:59-344373 DEBUG    APIRoute(name=get_samples path=/api/samples/{filename} method={'GET'})
16:50:59-344938 DEBUG    APIRoute(name=post_webhook path=/api/webhook method={'POST'})
16:50:59-345689 INFO     App(ready=True)
16:50:59-535842 INFO     IP(port=8080 external=None public=94.250.189.3)
16:50:59-555275 DEBUG    FastAPI({'debug': False, 'title': 'Echonos.AI Webhook Test Server', 'summary': None, 'description': '', 'version': '0.1.0', 'terms_of_service': None, 'contact': None, 'license_info': None, 'openapi_url': '/openapi.json', 'openapi_tags': None, 'root_path_in_servers': True, 'docs_url': '/docs', 'redoc_url': '/redoc', 'swagger_ui_oauth2_redirect_url': '/docs/oauth2-redirect', 'swagger_ui_init_oauth': None, 'swagger_ui_parameters': None, 'servers': [],
                         'separate_input_output_schemas': True, 'openapi_external_docs': None, 'extra': {}, 'openapi_version': '3.1.0', 'openapi_schema': None, '_openapi_routes_version': None, 'webhooks': <fastapi.routing.APIRouter object at 0x7af2b45c5a90>, 'root_path': '', 'state': <starlette.datastructures.State object at 0x7af2b46f9e80>, 'dependency_overrides': {}, 'router': <fastapi.routing.APIRouter object at 0x7af2b50fedb0>, 'exception_handlers': {<class
                         'starlette.exceptions.HTTPException'>: <function http_exception_handler at 0x7af2b38dfe20>, <class 'fastapi.exceptions.RequestValidationError'>: <function request_validation_exception_handler at 0x7af2b38f1ee0>, <class 'fastapi.exceptions.WebSocketRequestValidationError'>: <function websocket_request_validation_exception_handler at 0x7af2b38f1f80>}, 'user_middleware': [Middleware(GZipMiddleware, minimum_size=2048), Middleware(BaseHTTPMiddleware,
                         dispatch=<function HTTPD.start_fastapi.<locals>.http_logger at 0x7af2b37f6b60>)], 'middleware_stack': <starlette.middleware.errors.ServerErrorMiddleware object at 0x7af2b2581d60>, 'openapi': <function HTTPD.start_swagger.<locals>.openapi at 0x7af2b37f6ac0>})
16:50:59-557198 DEBUG    FastAPI(uptime=0.26)
```
