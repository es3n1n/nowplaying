from io import BytesIO
from typing import Optional, Tuple

from loguru import logger

from ..external.song_link import get_song_link_info
from ..models.track import Track
from .abc import DownloaderABC
from .deezer import DeezerDownloader
from .soundcloud import SoundcloudDownloader
from .youtube import YoutubeDownloader


# Uses the same priority as declared
downloaders: list[DownloaderABC] = [
    DeezerDownloader(),
    SoundcloudDownloader(),
    YoutubeDownloader(),
]


async def download_mp3(track: Track) -> Tuple[str, Optional[BytesIO]]:
    result: Optional[BytesIO] = None

    info = await get_song_link_info(track.song_link)

    for downloader in downloaders:
        if downloader.platform not in info.platforms:
            continue

        platform = info.platforms[downloader.platform]

        logger.debug(f'Trying to download {platform.url} from {platform.platform.name}')
        result = await downloader.download_mp3(platform)

        if result is not None:
            break

    return info.thumbnail_url, result
