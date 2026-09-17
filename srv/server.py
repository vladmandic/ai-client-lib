import time
from threading import Thread

from .logger import log

if __name__ == "__main__":
    _title = 'Echonos.AI Webhook Test Server'
    log.info(f'App(name="{_title}")')

    # init http server
    from .httpd import HTTPD
    server = HTTPD(
        title=_title,
        http=8080,
        https=0,
        monitor=60
    )
    Thread(target=server.run, daemon=True).start()

    # mount api routes
    from .api import mount
    mount(server=server, prefix=server.prefix)
    for route in server.get_routes():
        log.debug(route)

    log.info('App(ready=True)')
    try:
        while True:
            time.sleep(server.monitor)
    except KeyboardInterrupt:
        log.info('App(exit=True)')
