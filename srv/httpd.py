# Generic HTTP/Rest API server using FastAPI and Uvicorn

import contextlib
import logging
import ssl
import time
from threading import Thread

import uvicorn
from fastapi import FastAPI, Request, Response

from .api import mount
from .logger import log


class HTTPD:
    uv: list[uvicorn.Server] = []
    app: FastAPI = None

    def __init__(self, title: str = '', http: int = 8080, https: int = 0, monitor: int = 60, prefix: str = '/api'):
        self.http = http
        self.https = https
        self.title = title
        self.monitor = monitor
        self.prefix = prefix
        self.time = time.time()
        # auth is enforced per-route via the require_auth dependency (see app/auth.py),
        # mirroring the Bearer/Firebase + service-account pattern used by the other services

        self.start_fastapi()
        self.start_swagger()
        self.setup_middleware()
        if self.http > 0:
            self.start_uvicorn(port=self.http, secure=False)
        if self.https > 0:
            self.start_uvicorn(port=self.https, secure=True)

    def run(self):
        for _server in self.uv:
            log.info(f'IP(port={_server.config.port} external={self.get_external_ip()} public={self.get_remote_ip()})')
            Thread(target=_server.run, daemon=True).start()
            # _server.run()

    def start_uvicorn(self, port: int, secure: bool = False):
        def monitor(_uv: uvicorn.Server):
            while True:
                log.debug(f'Uvicorn(active={_uv.started} port={_uv.config.port} requests={_uv.server_state.total_requests} connections={len(_uv.server_state.connections)} uptime={time.time() - self.time:.2f})')
                time.sleep(self.monitor)

        config = uvicorn.Config(
            app = self.app,
            host = "0.0.0.0",
            port = port,
            log_level = logging.WARNING,
            reload = True,
        )
        if secure:
            config.ssl_keyfile = 'cert/key.pem'
            config.ssl_certfile = 'cert/cert.pem'
        log.debug(f"Uvicorn(start=True, secure={secure} port={port})")
        log.debug(f'Uvicorn({vars(config)})')
        uv = uvicorn.Server(config)
        self.uv.append(uv)
        Thread(target=monitor, daemon=True, args=(uv,)).start()

    def start_fastapi(self):
        def monitor():
            while True:
                if self.app and self.app.state._state: # pylint: disable=protected-access
                    log.debug(f'FastAPI(state={vars(self.app.state)} uptime={time.time() - self.time:.2f})')
                time.sleep(self.monitor)

        @contextlib.asynccontextmanager
        async def lifespan(_app: FastAPI):
            log.debug(f'FastAPI({vars(_app)})')
            Thread(target=monitor, daemon=True).start()
            yield
            log.debug('End()')

        self.app = FastAPI(title=self.title, lifespan=lifespan)

        @self.app.middleware("http")
        async def http_logger(req: Request, call_next):
            ts = time.time()
            res: Response = await call_next(req)
            duration = str(round(time.time() - ts, 4))
            res.headers["X-Process-Time"] = duration
            endpoint = req.scope.get('path', 'unknown')
            log.debug('API(code={code} protocol={protocol}/{version} method={method} endpoint={endpoint} client={client} duration={duration})'.format( # pylint: disable=consider-using-f-string, logging-format-interpolation
                code = res.status_code,
                protocol = req.scope.get('scheme', 'unknown'),
                version = req.scope.get('http_version', '0.0'),
                method = req.scope.get('method', 'unknown'),
                client = req.scope.get('client', ('0:0.0.0', 0))[0],
                endpoint = endpoint,
                duration = duration,
            ))
            return res

    def setup_middleware(self):
        from fastapi.middleware.gzip import GZipMiddleware
        ssl._create_default_https_context = ssl._create_unverified_context # pylint: disable=protected-access
        uvicorn_logger=logging.getLogger("uvicorn.error")
        uvicorn_logger.disabled = True
        self.app.add_middleware(GZipMiddleware, minimum_size=2048)
        middleware = [m.cls.__name__ for m in self.app.user_middleware]
        log.debug(f'Middleware({middleware})')

    def start_swagger(self, url: str = '/swagger'):
        from fastapi.openapi.docs import get_swagger_ui_html
        from fastapi.openapi.utils import get_openapi
        # from fastapi.staticfiles import StaticFiles

        @self.app.get(url, include_in_schema=False)
        async def docs():
            return get_swagger_ui_html(
                openapi_url=self.app.openapi_url,
                title=self.title,
                # swagger_favicon_url="/assets/echonos.ico",
                # swagger_css_url="/assets/swagger.css",
                swagger_ui_parameters={
                    "syntaxHighlight": {"theme": "nord"},
                    "displayRequestDuration": True,
                    "showCommonExtensions": True,
                },
            )

        def openapi():
            if self.app.openapi_schema:
                return self.app.openapi_schema
            openapi_schema = get_openapi(
                title=self.title,
                version="0.0.1",
                description="",
                routes=self.app.routes,
            )
            self.app.openapi_schema = openapi_schema
            return self.app.openapi_schema

        # self.app.mount("/assets", StaticFiles(directory="assets"), name="assets")
        self.app.openapi = openapi
        uri = f'http://localhost:{self.http}'
        log.debug(f'Swagger(schema={self.app.openapi_url} url={uri}{url} docs={uri}{self.app.docs_url} redoc={uri}{self.app.redoc_url})')

    def get_external_ip(self):
        import socket
        ip_address = socket.gethostbyname(socket.gethostname())
        if ip_address.startswith('127.'):
            return None
        return ip_address

    def get_remote_ip(self):
        import requests
        response = requests.get('https://api.ipify.org?format=json', timeout=2)
        ip_address = response.json()['ip']
        return ip_address

    def get_routes(self):
        routes = [f'{route.__class__.__name__}(name={route.name} path={getattr(route, "path", None)} method={getattr(route, "methods", None)})' for route in self.app.routes]
        return routes

if __name__ == "__main__":
    _title = 'EchonosAI-Compress'
    log.info(f'App("{_title}")')
    httpd = HTTPD(title=_title, http=8080, https=8081, monitor=60)
    Thread(target=httpd.run, daemon=True).start()
    mount(httpd, httpd.prefix)
    for route in httpd.get_routes():
        log.info(route)
    while True:
        time.sleep(1)
