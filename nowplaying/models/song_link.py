from pydantic import BaseModel

from ..enums.platform_type import SongLinkPlatformType


class SongLinkPlatform(BaseModel):
    platform: SongLinkPlatformType
    url: str


class SongLinkInfo(BaseModel):
    platforms: dict[SongLinkPlatformType, SongLinkPlatform] = {}
    thumbnail_url: str = ''
