import aiohttp
from aiohttp_socks import ProxyConnector
from yandex_music.client_async import ClientAsync as _ClientAsync
from yandex_music.exceptions import (
    BadRequestError,
    NetworkError,
    NotFoundError,
    TimedOutError,
    UnauthorizedError,
    YandexMusicError,
)
from yandex_music.utils.request import DEFAULT_TIMEOUT, USER_AGENT
from yandex_music.utils.request_async import Request as _Request

from nowplaying.core.config import config


class Request(_Request):
    def __init__(
        self,
        client: _ClientAsync = None,
        headers: dict[str, str] | None = None,
        proxy_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(client=client, headers=headers, timeout=timeout)

        self._proxy_url = proxy_url
        self._connector: ProxyConnector | None = None

    @property
    def connector(self) -> ProxyConnector | None:
        if self._connector is None and self._proxy_url:
            self._connector = ProxyConnector.from_url(self._proxy_url)
        return self._connector

    async def _request_wrapper(self, *args, **kwargs):  # noqa: C901, ANN003, ANN002, ANN202
        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        kwargs['headers']['User-Agent'] = USER_AGENT

        kwargs['timeout'] = aiohttp.ClientTimeout(total=self._timeout)
        kwargs['connector'] = self.connector

        try:
            async with aiohttp.request(*args, **kwargs) as _resp:
                resp = _resp
                content = await resp.content.read()
        except TimeoutError as e:
            raise TimedOutError from e
        except aiohttp.ClientError as e:
            raise NetworkError(e) from e

        if 200 <= resp.status <= 299:  # noqa:PLR2004
            return content

        try:
            parse = self._parse(content)
            message = parse.get_error()
        except YandexMusicError:
            message = 'Unknown HTTPError'

        if resp.status in (401, 403):
            raise UnauthorizedError(message)
        if resp.status == 400:  # noqa:PLR2004
            raise BadRequestError(message)
        if resp.status == 404:  # noqa:PLR2004
            raise NotFoundError(message)
        if resp.status in (409, 413):
            raise NetworkError(message)

        if resp.status == 502:  # noqa:PLR2004
            msg = 'Bad Gateway'
            raise NetworkError(msg)

        msg = f'{message} ({resp.status}): {content}'
        raise NetworkError(msg)

    def __del__(self) -> None:  # noqa:D105
        if self._connector:
            self._connector.close()


class ClientAsync(_ClientAsync):
    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        request: Request | None = None,
        language: str | None = 'ru',
        *,
        report_unknown_fields: bool = False,
    ) -> None:
        if not request:
            request = Request(proxy_url=config.YANDEX_PROXY)
        super().__init__(
            token=token,
            base_url=base_url,
            request=request,
            language=language,
            report_unknown_fields=report_unknown_fields,
        )
