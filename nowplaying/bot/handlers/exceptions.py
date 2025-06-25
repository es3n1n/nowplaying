from typing import cast

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, InlineQueryResultArticle, InputTextMessageContent

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.reporter import report_error
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.exceptions.platforms import (
    PlatformInvalidAuthCodeError,
    PlatformTemporarilyUnavailableError,
    PlatformTokenInvalidateError,
)
from nowplaying.util.logger import logger


AUTH_CODE_ERROR_MSG = 'Error! Unable to authorize in {platform}, please try again.'


async def send_auth_code_error_msg(exc: PlatformInvalidAuthCodeError) -> None:
    await bot.send_message(
        exc.telegram_id,
        AUTH_CODE_ERROR_MSG.format(platform=exc.platform.name.capitalize()),
    )


async def reply_to_event(event: ErrorEvent, message: str) -> None:
    if event.update.message is not None:
        try:
            await bot.send_message(
                chat_id=event.update.message.chat.id,
                text=message,
                reply_to_message_id=event.update.message.message_id,
            )
        except TelegramAPIError:
            return
        return

    if event.update.inline_query is not None:
        try:
            await bot.answer_inline_query(
                event.update.inline_query.id,
                results=[
                    InlineQueryResultArticle(
                        id='0',
                        title=message,
                        input_message_content=InputTextMessageContent(
                            message_text=message,
                        ),
                    ),
                ],
            )
        except TelegramAPIError:
            return
        return


@dp.error(ExceptionTypeFilter(PlatformInvalidAuthCodeError))
async def on_invalid_auth_code_error(event: ErrorEvent) -> bool:
    exc = cast(PlatformInvalidAuthCodeError, event.exception)

    await reply_to_event(event, AUTH_CODE_ERROR_MSG.format(platform=exc.platform.name.capitalize()))
    return True


@dp.error(ExceptionTypeFilter(PlatformTokenInvalidateError))
async def on_token_invalidation(event: ErrorEvent) -> bool:
    exc = cast(PlatformTokenInvalidateError, event.exception)

    logger.opt(exception=exc).warning('Invalidating platform session')
    await reply_to_event(
        event,
        f'Your {exc.platform.name.capitalize()} session has expired/got invalidated, please authorize again.'.strip(),
    )

    await db.delete_user_token(exc.telegram_id, exc.platform)
    return True


@dp.error(ExceptionTypeFilter(PlatformTemporarilyUnavailableError))
async def on_platform_unavailable(event: ErrorEvent) -> bool:
    exc = cast(PlatformTemporarilyUnavailableError, event.exception)

    message: str = f'Sorry, but it seems like {exc.platform.name.capitalize()} API is down\n'
    message += 'Try again later'
    await reply_to_event(event, message)
    return True


@dp.error(ExceptionTypeFilter(ExceptionGroup))
async def on_exception_group(event: ErrorEvent) -> bool:
    exc = cast(ExceptionGroup, event.exception)

    for nested_exc in exc.exceptions:
        nested_event = ErrorEvent(
            update=event.update,
            exception=nested_exc,
        )

        # TODO(es3n1n): feed them back to the dp
        if isinstance(nested_exc, PlatformInvalidAuthCodeError):
            return await on_invalid_auth_code_error(nested_event)

        if isinstance(nested_exc, PlatformTokenInvalidateError):
            return await on_token_invalidation(nested_event)

        if isinstance(nested_exc, PlatformTemporarilyUnavailableError):
            return await on_platform_unavailable(nested_event)

    return await fallback_error_handler(event)


@dp.error()
async def fallback_error_handler(event: ErrorEvent) -> bool:
    if (
        isinstance(event.exception, TelegramBadRequest)
        and 'query is too old and response timeout' in event.exception.message
    ):
        # There is nothing we can do about this,
        # since most likely this error occurs because of the long responses from platforms
        return False

    if isinstance(event.exception, TelegramForbiddenError) and 'bot was blocked by the user' in event.exception.message:
        # There's a telegram bug where people that blocked the bot can still send a message to it
        # using the start button that shows up in the inline menu, and the bot will try to respond to it.
        return False

    await reply_to_event(event, f'Something went wrong (┛ಠ_ಠ)┛彡┻━┻\nContact @{config.DEVELOPER_USERNAME}')

    message: str = 'Something went wrong!\n'
    message += f'Update: {event.update.model_dump_json(indent=3)}'
    await report_error(message, event.exception)
    return False
