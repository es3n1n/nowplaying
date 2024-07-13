from asyncio import create_task
from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional

from yt_dlp import DownloadError, YoutubeDL

from ..bot.reporter import report_error
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

        io = BytesIO()
        io.close = lambda: None  # type: ignore
        with redirect_stdout(io):  # type: ignore
            with YoutubeDL(params={
                'format': 'bestaudio/best',
                'geo_bypass': True,
                'nocheckcertificate': True,
                'outtmpl': '-',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    },
                ],
                'logger': YoutubeDLLogger,
            }) as ydl:
                try:
                    result_stat: int = ydl.download(url_list=[platform.url])
                except DownloadError:
                    return None

        if result_stat != 0:
            return None

        io.seek(0)
        return io
