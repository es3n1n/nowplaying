from collections.abc import AsyncIterable
from typing import NamedTuple

import pytest

from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTokenInvalidateError
from nowplaying.util.exceptions import rethrow_platform_error


class PlatformTestError(Exception):
    """Platform error."""


class Context(NamedTuple):
    telegram_id: int


ctx_to_pass = Context(123)


@pytest.mark.asyncio
async def test_rethrow() -> None:
    rethrown: bool = False

    @rethrow_platform_error(PlatformTestError, SongLinkPlatformType.UNKNOWN)
    async def rethrow_me(ctx: Context) -> None:
        raise PlatformTestError(str(ctx.telegram_id))

    try:
        await rethrow_me(ctx_to_pass)
    except PlatformTokenInvalidateError:
        rethrown = True

    assert rethrown


@pytest.mark.asyncio
async def test_rethrow_aiter() -> None:
    rethrown: bool = False

    @rethrow_platform_error(PlatformTestError, SongLinkPlatformType.UNKNOWN)
    async def rethrow_me_aiter(ctx: Context) -> AsyncIterable[None]:
        yield None
        raise PlatformTestError(str(ctx.telegram_id))

    try:
        async for dummy_item in rethrow_me_aiter(ctx_to_pass):
            assert dummy_item is None
    except PlatformTokenInvalidateError:
        rethrown = True

    assert rethrown
