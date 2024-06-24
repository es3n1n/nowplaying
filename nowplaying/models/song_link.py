from dataclasses import field

from pydantic import BaseModel

from ..enums.platform_type import SongLinkPlatformType


class SongLinkPlatform(BaseModel):
    platform: SongLinkPlatformType
    url: str


class SongLinkInfo(BaseModel):
    platforms: dict[SongLinkPlatformType, SongLinkPlatform] = field(default={})
    thumbnail_url: str = field(default='')
