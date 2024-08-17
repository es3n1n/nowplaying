from typing import cast

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
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,  # noqa: ASYNC109
    ) -> TelegramType:
        session = await self.create_session()

        url = self.api.api_url(token=bot.token, method=method.__api_method__)
        form = self.build_form_data(bot=bot, method=method)

        if config.BOT_LOG_REQUESTS and method.__api_method__ != 'getUpdates':
            logger.info(f'Executing {url} with form {method.model_dump()}')

        try:
            async with session.post(
                url,
                data=form,
                timeout=self.timeout if timeout is None else timeout,  # type: ignore[arg-type]
            ) as resp:
                raw_result = await resp.text()
        except TimeoutError as err:
            raise TelegramNetworkError(method=method, message='Request timeout error') from err
        except ClientError as exc:
            raise TelegramNetworkError(method=method, message=f'{type(exc).__name__}: {exc}') from exc

        response = self.check_response(
            bot=bot,
            method=method,
            status_code=resp.status,
            content=raw_result,
        )
        return cast(TelegramType, response.result)
