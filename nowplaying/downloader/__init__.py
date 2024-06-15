from io import BytesIO
from typing import Optional

from loguru import logger

from ..core.song_link import get_song_link_platforms
from ..models.track import Track
from .abc import DownloaderABC
from .deezer import DeezerDownloader
from .soundcloud import SoundcloudDownloader
from .youtube import YoutubeDownloader


downloaders: list[DownloaderABC] = [
    DeezerDownloader(),
    YoutubeDownloader(),
    SoundcloudDownloader(),
]


async def download_mp3(track: Track) -> Optional[BytesIO]:
    result: Optional[BytesIO] = None

    platforms = await get_song_link_platforms(track.song_link)

    for downloader in downloaders:
        if downloader.platform not in platforms:
            continue

        platform = platforms[downloader.platform]

        logger.debug(f'Trying to download {platform.url} from {platform.platform.name}')
        result = await downloader.download_mp3(platform)

        if result is not None:
            break

    return result
