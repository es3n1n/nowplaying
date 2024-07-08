import logging
import sys

from aiogram import loggers as aiogram_loggers
from loguru import logger
from scdl import scdl
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
            level, record.getMessage(),
        )


def _filter_min_level(record: dict) -> bool:
    current_level_name: str = 'DEBUG' if config.is_dev_env else 'INFO'
    current_level: int = logger.level(current_level_name).no
    return record['level'].no >= current_level


def _filter_stderr(record: dict) -> bool:
    return _filter_min_level(record)


def _filter_stdout(record: dict) -> bool:
    record_no: int = record['level'].no
    error_no: int = logger.level('ERROR').no
    return _filter_min_level(record) and record_no != error_no


def init_logger() -> None:
    level = logging.DEBUG if config.is_dev_env else logging.INFO

    loguru_handler = LoguruHandler()

    # No need to output scdl logs in production
    scdl.logger.setLevel(level=logging.DEBUG if config.is_dev_env else logging.ERROR)
    scdl.logger.handlers.clear()

    aiogram_loggers.event.setLevel(level=level)
    aiogram_loggers.dispatcher.setLevel(level=level)
    logging.basicConfig(handlers=[loguru_handler])

    for key in LOGGING_CONFIG['handlers'].keys():
        handler_conf = LOGGING_CONFIG['handlers'][key]

        handler_conf['class'] = 'nowplaying.util.logger.LoguruHandler'
        if 'stream' in handler_conf:
            handler_conf.pop('stream')

    fmt = (
        '<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
        + '<level>{message}</level>'
    )

    logger.remove()
    logger.configure(handlers=[
        {'sink': sys.stderr, 'level': 'ERROR', 'format': fmt, 'filter': _filter_stderr},
        {'sink': sys.stdout, 'format': fmt, 'filter': _filter_stdout},
    ])


init_logger()
