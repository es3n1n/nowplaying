from enum import Enum, unique


# No, this is not the same thing as `SongLinkPlatformType`. See `song_link_parsers.py`


@unique
class ResolvedPlatformType(str, Enum):
    AMAZON_MUSIC = 'amazon'
    AUDIOMACK = 'audiomack'
    AUDIUS = 'audius'
    BANDCAMP = 'bandcamp'
    BOOM_PLAY = 'boomplay'
    DEEZER = 'deezer'
    ITUNES = 'itunes'
    NAPSTER = 'napster'
    PANDORA = 'pandora'
    SOUNDCLOUD = 'soundcloud'
    SPINRILLA = 'spinrilla'
    SPOTIFY = 'spotify'
    TIDAL = 'tidal'
    YANDEX = 'yandex'
    YOUTUBE = 'youtube'
