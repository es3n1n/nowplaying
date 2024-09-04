from dataclasses import dataclass
from functools import cache
from time import time

import orjson
from aiohttp import ClientError, ClientSession
from loguru import logger

from nowplaying.core.config import config
from nowplaying.util.dns import select_url
from nowplaying.util.http import STATUS_OK, get_headers


@dataclass(frozen=True)
class DownloadedMp3:
    thumbnail_url: str | None = None
    mp3_data: bytes | None = None
    error: str | None = None


UNKNOWN_ERROR = f'Unknown error, contact @{config.DEVELOPER_USERNAME}'


@cache
def get_udownloader_base() -> str:
    return select_url(config.UDOWNLOADER_DOCKER_BASE_URL, config.UDOWNLOADER_BASE_URL)


# For now, only downloading from youtube via song.link is supported
async def download_mp3(song_link_url: str) -> DownloadedMp3:
    start_time = time()
    async with ClientSession(headers=get_headers()) as session:
        try:
            async with session.post(
                f'{get_udownloader_base()}/v1/mp3/by_songlink',
                json={'url': song_link_url},
            ) as response:
                if response.status != STATUS_OK:
                    bytes_data = await response.read()
                    try:
                        json_data = orjson.loads(bytes_data)
                    except orjson.JSONDecodeError:
                        return DownloadedMp3(error=UNKNOWN_ERROR)

                    return DownloadedMp3(error=json_data.get('detail', UNKNOWN_ERROR))

                serve_time = response.headers.get('x-serve-time', 'unknown')
                thumbnail = response.headers.get('x-thumbnail-url')
                mp3_data = await response.read()
        except ClientError:
            return DownloadedMp3(error='udownloader is unavailable')

    logger.info(
        f'Downloaded {song_link_url} from youtube via udownloader in {(time() - start_time) * 100:.1f}ms '
        f'(served in {serve_time})'
    )
    return DownloadedMp3(
        thumbnail_url=thumbnail,
        mp3_data=mp3_data,
    )
