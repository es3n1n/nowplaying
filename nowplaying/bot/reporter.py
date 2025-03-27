from aiogram.exceptions import AiogramError
from aiogram.types import BufferedInputFile
from loguru import logger

from nowplaying.core.config import config

from .bot import bot


TEXT_MESSAGE_LIMIT: int = 500


async def report_to_dev(message: str) -> None:
    if not config.BOT_TELEGRAM_ERROR_REPORTING:
        return

    try:
        if len(message) > TEXT_MESSAGE_LIMIT:
            await bot.send_document(
                chat_id=config.BOT_DEV_CHAT_ID,
                document=BufferedInputFile(file=message.encode(), filename='log.txt'),
                caption='Something went wrong!!!',
            )
            return

        await bot.send_message(
            chat_id=config.BOT_DEV_CHAT_ID,
            text=message,
        )
    except AiogramError as exc:
        logger.opt(exception=exc).error('Unable to report to dev')


async def report_error(message: str, exception: Exception | None = None) -> None:
    if isinstance(exception, ExceptionGroup):
        for exc in exception.exceptions:
            await report_error(message, exc)
        return

    logger.opt(exception=exception).error(message)
    try:
        await report_to_dev(message + f'\nException: {exception}')
    except AiogramError as exc:
        logger.opt(exception=exc).error('Unable to report to dev')
