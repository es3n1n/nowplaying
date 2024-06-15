from io import BytesIO
from os import remove
from typing import Optional

from youtube_dl import YoutubeDL

from ..models.song_link_platform import SongLinkPlatform, SongLinkPlatformType
from ..util.fs import temp_file
from ..util.logger import logger
from .abc import DownloaderABC


class YoutubeDownloader(DownloaderABC):
    platform = SongLinkPlatformType.YOUTUBE

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

        result = temp_file('.mp3')
        with YoutubeDL(params={
            'outtmpl': str((result.parent / result.stem).absolute()),
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }
            ],
        }) as ydl:
            if ydl.download(url_list=[platform.url]) != 0:
                return None

        # fixme: @es3n1n: fix this epic overhead
        io = BytesIO()
        with open(result, 'rb') as f:
            io.write(f.read())

        io.seek(0)
        remove(result)
        return io
