from asyncio import create_task
from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional, Type

from yt_dlp import DownloadError, YoutubeDL

from ..bot.reporter import report_error
from ..core.config import config
from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
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


class YoutubeDownloader(DownloaderABC):
    platform = SongLinkPlatformType.YOUTUBE

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

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
