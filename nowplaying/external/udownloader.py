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
class DownloadedSong:
    file_extension: str | None = None
    thumbnail_url: str | None = None
    duration_sec: int | None = None
    data: bytes | None = None
    quality_id: str = 'UNKNOWN'
    platform_name: str = 'UNKNOWN'
    error: str | None = None


UNKNOWN_ERROR = f'Unknown error, contact @{config.DEVELOPER_USERNAME}'


@cache
def get_udownloader_base() -> str:
    return select_url(config.UDOWNLOADER_DOCKER_BASE_URL, config.UDOWNLOADER_BASE_URL)


# For now, only downloading from youtube via song.link is supported
async def download(song_link_url: str) -> DownloadedSong:
    start_time = time()
    async with ClientSession(headers=get_headers()) as session:
        try:
            async with session.post(
                f'{get_udownloader_base()}/v1/download/by_songlink',
                json={'url': song_link_url},
            ) as response:
                if response.status != STATUS_OK:
                    bytes_data = await response.read()
                    try:
                        json_data = orjson.loads(bytes_data)
                    except orjson.JSONDecodeError:
                        return DownloadedSong(error=UNKNOWN_ERROR)

                    return DownloadedSong(error=json_data.get('detail', UNKNOWN_ERROR))

                serve_time = response.headers.get('x-serve-time', 'unknown')
                thumbnail = response.headers.get('x-thumbnail-url')
                file_extension = response.headers.get('x-file-extension')
                duration_sec = int(response.headers['x-duration-seconds'])
                quality_id = response.headers.get('x-file-quality', 'UNKNOWN')
                platform_name = response.headers.get('x-downloaded-from', 'YOUTUBE')
                data = await response.read()
        except ClientError:
            return DownloadedSong(error='udownloader is unavailable')

    logger.info(
        f'Downloaded {song_link_url} via udownloader in {(time() - start_time) * 100:.1f}ms '
        f'(served in {serve_time})'
    )
    return DownloadedSong(
        file_extension=file_extension,
        thumbnail_url=thumbnail,
        data=data,
        duration_sec=duration_sec,
        quality_id=quality_id,
        platform_name=platform_name,
    )
