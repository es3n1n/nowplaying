import asyncio
from typing import Optional, cast

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiohttp import ClientError
from loguru import logger

from nowplaying.core.config import config


class BotSession(AiohttpSession):
    async def make_request(
        self, bot: Bot, method: TelegramMethod[TelegramType], timeout: Optional[int] = None,
    ) -> TelegramType:
        session = await self.create_session()

        url = self.api.api_url(token=bot.token, method=method.__api_method__)
        form = self.build_form_data(bot=bot, method=method)

        if config.BOT_LOG_REQUESTS and method.__api_method__ != 'getUpdates':
            logger.info(f'Executing {url} with form {method.model_dump()}')

        try:
            async with session.post(
                url, data=form, timeout=self.timeout if timeout is None else timeout,
            ) as resp:
                raw_result = await resp.text()
        except asyncio.TimeoutError:
            raise TelegramNetworkError(method=method, message='Request timeout error')
        except ClientError as exc:
            raise TelegramNetworkError(method=method, message=f'{type(exc).__name__}: {exc}')

        response = self.check_response(
            bot=bot, method=method, status_code=resp.status, content=raw_result,  # noqa: WPS441
        )
        return cast(TelegramType, response.result)
