from asyncio import sleep
from typing import AsyncIterator


class OutOfRetriesError(Exception):
    """ """


async def retry(max_retries: int) -> AsyncIterator[int]:
    for index in range(max_retries):
        if index:
            await sleep(0.5 * index)

        yield index

    raise OutOfRetriesError()
