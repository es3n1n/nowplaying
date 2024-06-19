import logging
import sys

import aiogram.loggers
from loguru import logger
from uvicorn.config import LOGGING_CONFIG

from ..core.config import config


class LoguruHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelname

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            if frame.f_back is None:
                break

            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def init_logger() -> None:
    level = logging.DEBUG if config.dev_env else logging.INFO

    loguru_handler = LoguruHandler()

    aiogram.loggers.event.setLevel(level=level)
    aiogram.loggers.dispatcher.setLevel(level=level)
    logging.basicConfig(handlers=[loguru_handler])

    for _, v in LOGGING_CONFIG['handlers'].items():
        v['class'] = 'nowplaying.util.logger.LoguruHandler'
        if 'stream' in v:
            del v['stream']

    def filter_min_level(record: dict) -> bool:
        return record['level'].no >= logger.level('DEBUG' if config.dev_env else 'INFO').no

    def filter_stderr(record: dict) -> bool:
        return filter_min_level(record)

    def filter_stdout(record: dict) -> bool:
        return filter_min_level(record) and record['level'].no != logger.level('ERROR').no

    fmt = '<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - ' \
          '<level>{message}</level>'

    logger.remove()
    logger.configure(handlers=[
        {'sink': sys.stderr, 'level': 'ERROR', 'format': fmt, 'filter': filter_stderr},
        {'sink': sys.stdout, 'format': fmt, 'filter': filter_stdout}
    ])


init_logger()
