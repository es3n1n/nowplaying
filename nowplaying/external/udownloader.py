from asyncio import sleep
from dataclasses import dataclass
from functools import cache
from time import perf_counter
from typing import TypedDict

import orjson
from aiohttp import ClientError, ClientSession
from loguru import logger

from nowplaying.core.config import config
from nowplaying.util.dns import select_url
from nowplaying.util.http import STATUS_OK, get_headers


class SongQualityInfo(TypedDict):
    bit_depth: int | None
    bitrate_kbps: int
    sample_rate_khz: int
    highest_available: bool


@dataclass(frozen=True)
class DownloadedSong:
    file_extension: str
    thumbnail_url: str

    quality: SongQualityInfo
    duration_sec: int

    data: bytes

    platform_name: str = 'UNKNOWN'


class UdownloaderError(Exception):
    """Base class for all udownloader exceptions."""


class UdownloaderNetworkError(UdownloaderError):
    """Timeout, unreachable, etc."""


UNKNOWN_ERROR = f'Unknown error, contact @{config.DEVELOPER_USERNAME}'


@cache
def get_udownloader_base() -> str:
    return select_url(config.UDOWNLOADER_DOCKER_BASE_URL, config.UDOWNLOADER_BASE_URL)


async def _download_by_songlink(body: dict[str, str | bool]) -> DownloadedSong:
    start_time = perf_counter()
    async with ClientSession(headers=get_headers()) as session:
        try:
            async with session.post(
                f'{get_udownloader_base()}/v1/download/by_songlink',
                json=body,
            ) as response:
                if response.status != STATUS_OK:
                    bytes_data = await response.read()
                    try:
                        json_data = orjson.loads(bytes_data)
                    except orjson.JSONDecodeError as err:
                        raise UdownloaderError(UNKNOWN_ERROR) from err

                    raise UdownloaderError(json_data.get('detail', UNKNOWN_ERROR))

                serve_time = response.headers['x-serve-time']
                thumbnail = response.headers['x-thumbnail-url']
                file_extension = response.headers['x-file-extension']
                duration_sec = int(response.headers['x-duration-seconds'])
                quality_json = orjson.loads(response.headers['x-file-quality'])
                platform_name = response.headers['x-downloaded-from']
                data = await response.read()
        except (ClientError, TimeoutError, OSError, orjson.JSONDecodeError) as err:
            err_msg = 'udownloader is unavailable'
            raise UdownloaderNetworkError(err_msg) from err

    end = perf_counter()
    logger.info(f'Downloaded {body} via udownloader in {(end - start_time) * 1000:.1f}ms ' f'(served in {serve_time})')
    return DownloadedSong(
        file_extension=file_extension,
        thumbnail_url=thumbnail,
        data=data,
        duration_sec=duration_sec,
        quality=quality_json,
        platform_name=platform_name,
    )


async def download(song_link_url: str, *, download_flac: bool, fast_route: bool) -> DownloadedSong:
    last_exception: UdownloaderNetworkError | None = None

    for i in range(config.UDOWNLOADER_RETRIES):
        try:
            return await _download_by_songlink(
                {
                    'url': song_link_url,
                    'download_flac': download_flac,
                    'skip_song_link': fast_route,
                }
            )
        except UdownloaderNetworkError as err:
            # Retry only on network errors
            last_exception = err
            logger.opt(exception=err).warning(
                f'Got a network error while downloading {song_link_url!r}. Delaying for {i}s'
            )
            await sleep(i)
            continue

    if last_exception:
        raise last_exception

    raise UdownloaderNetworkError(UNKNOWN_ERROR)
