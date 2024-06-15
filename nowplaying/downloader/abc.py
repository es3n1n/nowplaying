from abc import ABC

from ..models.song_link_platform import SongLinkPlatformType


class DownloaderABC(ABC):
    platform: SongLinkPlatformType = SongLinkPlatformType.UNKNOWN
