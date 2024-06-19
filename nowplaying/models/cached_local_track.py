from dataclasses import dataclass

from ..enums.platform_type import SongLinkPlatformType


@dataclass
class CachedLocalTrack:
    id: str
    platform_type: SongLinkPlatformType
    url: str
    artist: str
    name: str
