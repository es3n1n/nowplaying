from asyncio import create_task
from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional, Type

import orjson
from httpx import AsyncClient, Timeout
from yt_dlp import DownloadError, YoutubeDL

from ..bot.reporter import report_error
from ..core.config import config
from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.http import STATUS_OK
from ..util.logger import logger
from .abc import DownloaderABC


class YoutubeDLLogger:
    @staticmethod
    def debug(msg: str):  # noqa: WPS602
        """Do nothing."""

    @staticmethod
    def warning(msg: str):  # noqa: WPS602
        logger.warning(msg)

    @staticmethod
    def error(msg: str):  # noqa: WPS602
        create_task(report_error(f'Youtube error: {msg}'))


async def download_through_cobalt(platform: SongLinkPlatform) -> Optional[BytesIO]:
    # Might be useful: https://instances.hyper.lol/instances.json
    async with AsyncClient(
        headers={
            'User-Agent': 'playinnowbot/1.0',
            'Accept': 'application/json',
        },
        timeout=Timeout(timeout=60),
    ) as client:
        json_response = await client.post(f'{config.COBALT_API_BASE_URL}/api/json', json={
            'isAudioOnly': 'true',
            'url': platform.url,
            'aFormat': 'mp3',
        })
        if json_response.status_code != STATUS_OK:
            await report_error(f'Got {json_response.status_code} from cobalt: {json_response.text}')
            return None

        try:
            json_data = orjson.loads(json_response.content)
        except orjson.JSONDecodeError:
            await report_error(f'Got unsupported json from cobalt: {json_response.text}')
            return None

        status: str = json_data.get('status', 'error')
        url: str | None = json_data.get('url', None)
        if status in {'error', 'rate-limit'} or url is None:
            await report_error(f'Got an error/ratelimit from cobalt: {json_response.text}')
            return None

        audio_data = await client.get(url)
        return BytesIO(audio_data.content)


async def download_through_youtube_dl(platform: SongLinkPlatform) -> Optional[BytesIO]:
    youtube_params: dict[str, str | bool | list[dict] | Type] = {
        'format': 'bestaudio/best',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'outtmpl': '-',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
        ],
        'logger': YoutubeDLLogger,
    }

    if config.YOUTUBE_COOKIES_PATH is not None:
        youtube_params['cookiefile'] = config.YOUTUBE_COOKIES_PATH

    io = BytesIO()
    io.close = lambda: None  # type: ignore
    with redirect_stdout(io):  # type: ignore
        with YoutubeDL(params=youtube_params) as ydl:
            try:
                result_stat: int = ydl.download(url_list=[platform.url])
            except DownloadError:
                return None

    if result_stat != 0:
        return None

    io.seek(0)
    return io


class YoutubeDownloader(DownloaderABC):
    platform = SongLinkPlatformType.YOUTUBE

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

        io = await download_through_cobalt(platform)
        io = io or await download_through_youtube_dl(platform)

        if io is None:
            return None

        return io
