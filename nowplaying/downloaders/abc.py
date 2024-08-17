from abc import ABC, abstractmethod
from io import BytesIO

from nowplaying.models.song_link import SongLinkPlatform, SongLinkPlatformType


class DownloaderABC(ABC):
    platform: SongLinkPlatformType = SongLinkPlatformType.UNKNOWN

    @abstractmethod
    async def download_mp3(self, platform: SongLinkPlatform) -> BytesIO | None:
        """Download mp3 for a given platform source."""
