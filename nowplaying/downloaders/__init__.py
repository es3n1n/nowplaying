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
    YoutubeDownloader(),
    SoundcloudDownloader(),
]


async def download_mp3(track: Track) -> Tuple[str, Optional[BytesIO]]:
    result_mp3: Optional[BytesIO] = None

    song_link_info = await get_song_link_info(track.song_link)

    for downloader in downloaders:
        if downloader.platform not in song_link_info.platforms:
            continue

        platform = song_link_info.platforms[downloader.platform]

        logger.debug(f'Trying to download {platform.url} from {platform.platform.name}')
        result_mp3 = await downloader.download_mp3(platform)

        if result_mp3 is not None:
            break

    return song_link_info.thumbnail_url, result_mp3
