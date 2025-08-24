from enum import Enum, unique


@unique
class SongLinkPlatformType(Enum):
    UNKNOWN = 'unknown'

    AMAZON_MUSIC = 'amazonMusic'
    AMAZON_STORE = 'amazonStore'
    ANGHAMI = 'anghami'
    APPLE = 'appleMusic'
    AUDIOMACK = 'audiomack'
    AUDIUS = 'audius'
    BANDCAMP = 'bandcamp'
    BOOM_PLAY = 'boomplay'
    DEEZER = 'deezer'
    GOOGLE = 'google'
    GOOGLE_STORE = 'googleStore'
    ITUNES = 'itunes'
    NAPSTER = 'napster'
    PANDORA = 'pandora'
    SOUNDCLOUD = 'soundcloud'
    SPINRILLA = 'spinrilla'
    SPOTIFY = 'spotify'
    TIDAL = 'tidal'
    YANDEX = 'yandex'
    YOUTUBE = 'youtube'
    YOUTUBE_MUSIC = 'youtubeMusic'

    # @fixme: @es3n1n: added by me
    LASTFM = 'lastfm'
