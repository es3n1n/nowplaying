from enum import Enum, unique


@unique
class SongLinkPlatformType(Enum):
    UNKNOWN: str = 'unknown'

    AMAZON_MUSIC: str = 'amazonMusic'
    AMAZON_STORE: str = 'amazonStore'
    ANGHAMI: str = 'anghami'
    APPLE: str = 'appleMusic'
    AUDIOMACK: str = 'audiomack'
    AUDIUS: str = 'audius'
    BANDCAMP: str = 'bandcamp'
    BOOM_PLAY: str = 'boomplay'
    DEEZER: str = 'deezer'
    GOOGLE: str = 'google'
    GOOGLE_STORE: str = 'googleStore'
    ITUNES: str = 'itunes'
    NAPSTER: str = 'napster'
    PANDORA: str = 'pandora'
    SOUNDCLOUD: str = 'soundcloud'
    SPINRILLA: str = 'spinrilla'
    SPOTIFY: str = 'spotify'
    TIDAL: str = 'tidal'
    YANDEX: str = 'yandex'
    YOUTUBE: str = 'youtube'
    YOUTUBE_MUSIC: str = 'youtubeMusic'

    # @fixme: @es3n1n: added by me
    LASTFM: str = 'lastfm'
