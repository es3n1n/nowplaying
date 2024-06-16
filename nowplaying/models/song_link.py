from enum import Enum

from pydantic import BaseModel


class SongLinkPlatformType(Enum):
    UNKNOWN: str = 'unknown'
    YOUTUBE: str = 'youtube'
    YOUTUBE_MUSIC: str = 'youtubeMusic'
    APPLE_MUSIC: str = 'appleMusic'
    SPOTIFY: str = 'spotify'
    PANDORA: str = 'pandora'
    DEEZER: str = 'deezer'
    SOUNDCLOUD: str = 'soundcloud'
    AMAZON_MUSIC: str = 'amazonMusic'
    TIDAL: str = 'tidal'
    NAPSTER: str = 'napster'
    YANDEX: str = 'yandex'
    BOOM_PLAY: str = 'boomplay'
    ANGHAMI: str = 'anghami'

    # @fixme: @es3n1n: added by me
    LASTFM: str = 'lastfm'


class SongLinkPlatform(BaseModel):
    platform: SongLinkPlatformType
    url: str


class SongLinkInfo(BaseModel):
    platforms: dict[SongLinkPlatformType, SongLinkPlatform]
    thumbnail_url: str