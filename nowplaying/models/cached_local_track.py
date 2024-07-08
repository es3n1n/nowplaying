from pydantic import BaseModel

from ..enums.platform_type import SongLinkPlatformType


class CachedLocalTrack(BaseModel):
    id: str
    platform_type: SongLinkPlatformType
    url: str
    artist: str
    name: str
