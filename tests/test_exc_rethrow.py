from collections import namedtuple
from typing import AsyncIterable

from pytest import mark

from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTokenInvalidateError
from nowplaying.util.exceptions import rethrow_platform_error


class PlatformTestError(Exception):
    """Platform error."""


Context = namedtuple('Context', ['telegram_id'])
ctx_to_pass = Context(123)


@mark.asyncio
async def test_rethrow() -> None:
    rethrown: bool = False

    @rethrow_platform_error(PlatformTestError, SongLinkPlatformType.UNKNOWN)
    async def rethrow_me(ctx: Context) -> None:
        raise PlatformTestError(str(ctx.telegram_id))

    try:
        await rethrow_me(ctx_to_pass)
    except Exception as e:
        rethrown = isinstance(e, PlatformTokenInvalidateError)

    assert rethrown


@mark.asyncio
async def test_rethrow_aiter() -> None:
    rethrown: bool = False

    @rethrow_platform_error(PlatformTestError, SongLinkPlatformType.UNKNOWN)
    async def rethrow_me_aiter(ctx: Context) -> AsyncIterable[None]:
        yield None
        raise PlatformTestError(str(ctx.telegram_id))

    try:
        async for dummy_item in rethrow_me_aiter(ctx_to_pass):
            assert dummy_item is None
    except Exception as e:
        rethrown = isinstance(e, PlatformTokenInvalidateError)

    assert rethrown

