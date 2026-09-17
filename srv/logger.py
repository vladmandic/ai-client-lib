import logging
import socket

from rich.console import Console
from rich.theme import Theme

log = logging.getLogger("aiventra")
hostname = socket.gethostname()
theme = Theme({
    "traceback.border": "black",
    "inspect.value.border": "black",
    "traceback.border.syntax_error": "dark_red",
    "logging.level.info": "blue_violet",
    "logging.level.debug": "purple4",
    "logging.level.trace": "dark_blue",
})
console = Console(
    log_time=True,
    log_time_format='%H:%M:%S-%f',
    tab_size=4,
    soft_wrap=True,
    safe_box=True,
    theme=theme,
)
initialized = False


def install_traceback(suppress: list = []):
    from rich.pretty import install as pretty_install
    from rich.traceback import install as traceback_install
    traceback_install(
        console=console,
        extra_lines=1,
        max_frames=16,
        width=console.width,
        word_wrap=False,
        indent_guides=False,
        show_locals=False,
        locals_hide_dunder=True,
        locals_hide_sunder=None,
        suppress=suppress,
    )
    pretty_install(console=console)


def init(log_file: str | None = None):
    from functools import partial, partialmethod
    from logging.handlers import RotatingFileHandler

    from rich import box
    from rich import print as rprint
    from rich.logging import RichHandler
    from rich.padding import Padding
    from rich.segment import Segment

    class RingBuffer(logging.StreamHandler):
        def __init__(self, capacity):
            super().__init__()
            self.capacity = capacity
            self.buffer = []
            self.formatter = logging.Formatter('{ "asctime":"%(asctime)s", "created":%(created)f, "pid":%(process)d, "level":"%(levelname)s", "module":"%(module)s", "msg":"%(message)s" }')

        def emit(self, record):
            if record.msg is not None and not isinstance(record.msg, str):
                record.msg = str(record.msg)
            try:
                record.msg = record.msg.replace('"', "'")
            except Exception:
                pass
            msg = self.format(record)
            self.buffer.append(msg)
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)

        def get(self):
            return self.buffer


    class LogFilter(logging.Filter):
        def __init__(self):
            super().__init__()

        def filter(self, record):
            return len(record.getMessage()) > 2

    def override_padding(self, console, options): # pylint: disable=redefined-outer-name
        style = console.get_style(self.style)
        width = options.max_width
        self.left = 0
        render_options = options.update_width(width - self.left - self.right)
        if render_options.height is not None:
            render_options = render_options.update_height(height=render_options.height - self.top - self.bottom)
        lines = console.render_lines(self.renderable, render_options, style=style, pad=False)
        _Segment = Segment
        left = _Segment(" " * self.left, style) if self.left else None
        right = [_Segment.line()]
        blank_line: list[Segment] | None = None
        if self.top:
            blank_line = [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.top
        if left:
            for line in lines:
                yield left
                yield from line
                yield from right
        else:
            for line in lines:
                yield from line
                yield from right
        if self.bottom:
            blank_line = blank_line or [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.bottom

    logging.TRACE = 25
    logging.addLevelName(logging.TRACE, 'TRACE')
    logging.Logger.trace = partialmethod(logging.Logger.log, logging.TRACE)
    logging.trace = partial(logging.log, logging.TRACE)

    level = logging.DEBUG
    log.setLevel(logging.DEBUG) # log to file is always at level debug
    log.print = rprint
    log.install = install_traceback
    log.init = init

    Padding.__rich_console__ = override_padding
    box.ROUNDED = box.SIMPLE

    logging.basicConfig(level=logging.ERROR, format='%(asctime)s | %(name)s | %(levelname)s | %(module)s | %(message)s', handlers=[logging.NullHandler()]) # redirect default logger to null
    install_traceback()
    while log.hasHandlers() and len(log.handlers) > 0:
        log.removeHandler(log.handlers[0])

    log_filter = LogFilter()
    # handlers
    rh = RichHandler(show_time=True, omit_repeated_times=False, show_level=True, show_path=False, markup=False, rich_tracebacks=True, log_time_format='%H:%M:%S-%f', level=level, console=console)
    rh.formatter = logging.Formatter('')
    rh.addFilter(log_filter)
    rh.setLevel(level)
    log.addHandler(rh)

    if log_file is not None:
        fh = RotatingFileHandler(log_file, maxBytes=32*1024*1024, backupCount=9, encoding='utf-8', delay=True) # 10MB default for log rotation
        fh.formatter = logging.Formatter('')
        fh.addFilter(log_filter)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)
        # fh.doRollover()

    rb = RingBuffer(100) # 100 entries default in log ring buffer
    rb.addFilter(log_filter)
    rb.setLevel(level)
    log.addHandler(rb)
    log.buffer = rb.buffer

    def quiet_log(quiet: bool=False, *args, **kwargs): # pylint: disable=redefined-outer-name,keyword-arg-before-vararg
        if not quiet:
            log.debug(*args, **kwargs)
    log.quiet = quiet_log

    # logging.getLogger("urllib3").setLevel(logging.ERROR)


if not initialized:
    init()
    initialized = True
