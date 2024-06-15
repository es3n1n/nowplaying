from io import BytesIO
from typing import Optional

from ..models.song_link_platform import SongLinkPlatform, SongLinkPlatformType
from .abc import DownloaderABC


class SoundcloudDownloader(DownloaderABC):
    platform = SongLinkPlatformType.SOUNDCLOUD

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        return None
