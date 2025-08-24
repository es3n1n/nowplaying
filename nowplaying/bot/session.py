from asyncio import sleep
from typing import Any, cast

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession, _ProxyType
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiohttp import ClientError, ClientSession
from loguru import logger

from nowplaying.bot.reporter import report_to_dev
from nowplaying.core.config import config
from nowplaying.util.dns import try_resolve_url


def get_self_hosted_api() -> TelegramAPIServer:
    if not try_resolve_url(config.LOCAL_TELEGRAM_API_BASE_URL):
        logger.warning('Unable to resolve self-hosted telegram api instance, falling back to the default one')
        return PRODUCTION

    logger.info('Successfully resolved the self-hosted telegram api instance')
    return TelegramAPIServer(
        base=config.LOCAL_TELEGRAM_API_BASE_URL + '/bot{token}/{method}',
        file=config.LOCAL_TELEGRAM_API_BASE_URL + '/file/bot{token}/{path}',
    )


class BotSession(AiohttpSession):
    def __init__(self, proxy: _ProxyType | None = None, limit: int = 100, **kwargs: Any) -> None:  # noqa: ANN401
        self._initialized_api = False

        super().__init__(proxy, limit, **kwargs)

    async def create_session(self) -> ClientSession:
        # We want to initialize this only when we need the bot.
        # By initializing this only once needed,
        # we avoid overhead from the unneeded dns resolves in multi-processed stuff
        if not self._initialized_api:
            self.api = get_self_hosted_api()
            self._initialized_api = True

        return await super().create_session()

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

        try:
            response = self.check_response(
                bot=bot,
                method=method,
                status_code=resp.status,
                content=raw_result,
            )
        except TelegramRetryAfter as exc:
            # Avoid report_to_dev, or something like that, otherwise we might enter a loop of flood-waits
            logger.warning(
                f'Got flood wait from telegram while requesting {method}, retrying after {exc.retry_after} seconds'
            )
            await sleep(exc.retry_after)
            return await self.make_request(bot, method, timeout)

        return cast(TelegramType, response.result)
