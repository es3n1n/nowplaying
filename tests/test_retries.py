from pytest import mark, raises

from nowplaying.util.retries import OutOfRetriesError, retry


@mark.asyncio
async def test_retry_basic() -> None:
    checked: bool = False

    async for i in retry(5):
        if i != 1:
            continue
        checked = True
        break

    assert checked


@mark.asyncio
async def test_retry_timeout() -> None:
    with raises(OutOfRetriesError):
        async for _ in retry(1):
            pass

