from aiogram.exceptions import TelegramAPIError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, InlineQueryResultArticle, InputTextMessageContent

from ...core.config import config
from ...core.database import db
from ...exceptions.platforms import PlatformInvalidAuthCodeError, PlatformTokenInvalidateError
from ...util.logger import logger
from ..bot import bot, dp


BROKE_MSG_TEXT: str = f'Something went wrong (┛ಠ_ಠ)┛彡┻━┻\nContact @{config.DEVELOPER_USERNAME}'


async def send_auth_code_error(exc: PlatformInvalidAuthCodeError) -> None:
    await bot.send_message(
        exc.telegram_id,
        f'Error! Unable to authorize in {exc.platform.value.capitalize()}, please try again.'
    )


@dp.error(ExceptionTypeFilter(PlatformInvalidAuthCodeError))
async def on_invalid_auth_code_error(event: ErrorEvent) -> bool:
    await send_auth_code_error(event.exception)  # type: ignore
    return True


@dp.error(ExceptionTypeFilter(PlatformTokenInvalidateError))
async def on_token_invalidation(event: ErrorEvent) -> bool:
    exc: PlatformTokenInvalidateError = event.exception  # type: ignore

    await bot.send_message(
        exc.telegram_id,
        f'Your {exc.platform.value.capitalize()} session has expired/got invalidated, please authorize again.'
    )
    db.delete_user_token(exc.telegram_id, exc.platform)
    return True


@dp.error()
async def fallback_error_handler(event: ErrorEvent) -> bool:
    if event.update.message is not None:
        logger.opt(exception=event.exception).error(
            f'Something broke in message handler!\n'
            f'Update: {event.update.model_dump_json(indent=3)}'
        )

        try:
            await bot.send_message(
                chat_id=event.update.message.chat.id,
                text=BROKE_MSG_TEXT,
                reply_to_message_id=event.update.message.message_id,
            )
        except TelegramAPIError:
            pass

        return True

    if event.update.inline_query is not None:
        logger.opt(exception=event.exception).error(
            f'Something broke in inline query handler!\n'
            f'Update: {event.update.model_dump_json(indent=3)}'
        )

        try:
            await bot.answer_inline_query(
                event.update.inline_query.id,
                results=[
                    InlineQueryResultArticle(
                        id='0',
                        title=f'Something went wrong, contact @{config.DEVELOPER_USERNAME}',
                        url=f'https://t.me/{config.DEVELOPER_USERNAME}',
                        input_message_content=InputTextMessageContent(
                            message_text=BROKE_MSG_TEXT
                        )
                    )
                ]
            )
        except TelegramAPIError:
            pass

        return True

    return False
