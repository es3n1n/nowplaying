import pytest

from nowplaying.util.retries import OutOfRetriesError, retry


@pytest.mark.asyncio
async def test_retry_basic() -> None:
    checked: bool = False

    async for i in retry(5):
        if i != 1:
            continue
        checked = True
        break

    assert checked


@pytest.mark.asyncio
async def test_retry_timeout() -> None:
    with pytest.raises(OutOfRetriesError):
        _ = [None async for _ in retry(1)]
