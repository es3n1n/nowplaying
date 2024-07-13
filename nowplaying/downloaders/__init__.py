from collections import OrderedDict
from io import BytesIO
from typing import Optional, Tuple

from loguru import logger

from ..enums.platform_type import SongLinkPlatformType
from ..external.song_link import get_song_link_info
from ..models.track import Track
from .abc import DownloaderABC
from .deezer import DeezerDownloader
from .soundcloud import SoundcloudDownloader
from .youtube import YoutubeDownloader


# Uses the same priority as declared
DOWNLOADER_CLASSES = (
    DeezerDownloader,
    SoundcloudDownloader,
    YoutubeDownloader,
)
DOWNLOADERS: OrderedDict[SongLinkPlatformType, DownloaderABC] = OrderedDict(
    (downloader_type.platform, downloader_type())  # type: ignore
    for downloader_type in DOWNLOADER_CLASSES
)


async def download_mp3(track: Track) -> Tuple[str, Optional[BytesIO]]:
    result_mp3: Optional[BytesIO] = None

    song_link_info = await get_song_link_info(track.song_link)

    for downloader_platform, downloader in DOWNLOADERS.items():
        if downloader_platform not in song_link_info.platforms:
            continue

        platform = song_link_info.platforms[downloader_platform]

        logger.debug(f'Trying to download {platform.url} from {platform.platform.name}')
        result_mp3 = await downloader.download_mp3(platform)

        if result_mp3 is not None and result_mp3.getvalue():
            break

    return song_link_info.thumbnail_url, result_mp3
