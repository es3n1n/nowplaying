from asyncio import create_task
from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional, Type

from httpx import AsyncClient, HTTPError, Timeout
from yt_dlp import DownloadError, YoutubeDL

from ..bot.reporter import report_error
from ..core.config import config
from ..external.cobalt import Cobalt
from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.logger import logger
from .abc import DownloaderABC


cobalt = Cobalt()
COBALT_RETRIES = 3


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
    stream: str | None = None

    # Retry with different instances
    for _ in range(COBALT_RETRIES):
        stream = await cobalt.get_mp3_stream_url(platform.url)

        if stream:
            break

        # Change instance on error
        await cobalt.re_roll_instance()

    # Still no stream
    if not stream:
        return None

    async with AsyncClient(
        timeout=Timeout(timeout=60),
    ) as client:
        try:
            audio_req = await client.get(stream)
            audio_data = audio_req.content
        except HTTPError:
            # huh??? http error? get banned then.
            audio_data = b''

        # Detect mp3 magic bytes, this is needed because for some reason some cobalt apis return an error as a string
        #   instead of the file we're requesting.
        if audio_data[:3] == b'ID3':
            return BytesIO(audio_data)

        if audio_data[:2] in {b'\xFF\xFB', b'\xFF\xF3', b'\xFF\xF2'}:
            return BytesIO(audio_data)

        # Ban this instance and reroll a new one
        await cobalt.re_roll_instance(ban_current=True)
        return await download_through_cobalt(platform)


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
