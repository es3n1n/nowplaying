from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional

from yt_dlp import DownloadError, YoutubeDL

from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.logger import logger
from .abc import DownloaderABC


class YoutubeDLLogger(object):
    @staticmethod
    def debug(msg: str):
        pass

    @staticmethod
    def warning(msg: str):
        logger.warning(msg)

    @staticmethod
    def error(msg: str):
        logger.error(msg)


class YoutubeDownloader(DownloaderABC):
    platform = SongLinkPlatformType.YOUTUBE

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

        io = BytesIO()
        io.close = lambda: None  # type: ignore
        with (redirect_stdout(io),  # type: ignore
              YoutubeDL(params={
                  'format': 'bestaudio/best',
                  'geo_bypass': True,
                  'nocheckcertificate': True,
                  'outtmpl': '-',
                  'postprocessors': [
                      {
                          'key': 'FFmpegExtractAudio',
                          'preferredcodec': 'mp3',
                      }
                  ],
                  'logger': YoutubeDLLogger
              }) as ydl):
            try:
                if ydl.download(url_list=[platform.url]) != 0:
                    return None
            except DownloadError:
                return None

        io.seek(0)
        return io
