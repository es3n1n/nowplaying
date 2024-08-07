from aiogram.exceptions import TelegramAPIError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, InlineQueryResultArticle, InputTextMessageContent

from ...core.config import config
from ...core.database import db
from ...enums.platform_type import SongLinkPlatformType
from ...exceptions.platforms import (
    PlatformInvalidAuthCodeError,
    PlatformTemporarilyUnavailableError,
    PlatformTokenInvalidateError,
)
from ...util.logger import logger
from ..bot import bot, dp
from ..reporter import report_error


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
                cache_time=1,
            )
        except TelegramAPIError:
            return
        return


@dp.error(ExceptionTypeFilter(PlatformInvalidAuthCodeError))
async def on_invalid_auth_code_error(event: ErrorEvent) -> bool:
    exc: PlatformInvalidAuthCodeError = event.exception  # type: ignore

    await reply_to_event(event, AUTH_CODE_ERROR_MSG.format(platform=exc.platform.name.capitalize()))
    return True


@dp.error(ExceptionTypeFilter(PlatformTokenInvalidateError))
async def on_token_invalidation(event: ErrorEvent) -> bool:
    exc: PlatformTokenInvalidateError = event.exception  # type: ignore

    footer: str = ''
    if exc.platform == SongLinkPlatformType.SPOTIFY:
        footer = (
            'This might be because spotify has not approved this application yet.\n'
            + f'There might be some free dev user slots for the application, dm @{config.DEVELOPER_USERNAME}'
        )

    logger.opt(exception=exc).warning('Invalidating platform session')
    await reply_to_event(
        event,
        (
            f'Your {exc.platform.name.capitalize()} session has expired/got invalidated, please authorize again.'
            + f'\n{footer}'
        ).strip(),
    )

    await db.delete_user_token(exc.telegram_id, exc.platform)
    return True


@dp.error(ExceptionTypeFilter(PlatformTemporarilyUnavailableError))
async def on_platform_unavailable(event: ErrorEvent) -> bool:
    exc: PlatformTemporarilyUnavailableError = event.exception  # type: ignore
    await reply_to_event(
        event,
        (
            f'Sorry, but it seems like {exc.platform.name.capitalize()} API is down'
            + '\nTry again later'
        ),
    )
    return True


@dp.error(ExceptionTypeFilter(ExceptionGroup))
async def on_exception_group(event: ErrorEvent) -> bool:
    exc: ExceptionGroup = event.exception  # type: ignore

    for nested_exc in exc.exceptions:
        nested_event = ErrorEvent(
            update=event.update,
            exception=nested_exc,
        )

        # todo: feed them back to the dp
        if isinstance(nested_exc, PlatformInvalidAuthCodeError):
            return await on_invalid_auth_code_error(nested_event)

        if isinstance(nested_exc, PlatformTokenInvalidateError):
            return await on_token_invalidation(nested_event)

        if isinstance(nested_exc, PlatformTemporarilyUnavailableError):
            return await on_platform_unavailable(nested_event)

    return await fallback_error_handler(event)


@dp.error()
async def fallback_error_handler(event: ErrorEvent) -> bool:
    await reply_to_event(event, f'Something went wrong (┛ಠ_ಠ)┛彡┻━┻\nContact @{config.DEVELOPER_USERNAME}')
    await report_error(
        f'Something went wrong!'
        f'Update: {event.update.model_dump_json(indent=3)}',
        event.exception,
    )
    return False
