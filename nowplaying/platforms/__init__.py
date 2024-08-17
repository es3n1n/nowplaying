from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track

from .abc import PlatformABC, PlatformClientABC
from .apple import ApplePlatform
from .lastfm import LastfmPlatform
from .spotify import SpotifyPlatform
from .yandex import YandexPlatform


spotify = SpotifyPlatform()
lastfm = LastfmPlatform()
apple = ApplePlatform()
yandex = YandexPlatform()

platforms: list[PlatformABC] = [
    spotify,
    lastfm,
    apple,
    yandex,
]


async def get_platform_from_telegram_id(telegram_id: int, platform_type: SongLinkPlatformType) -> PlatformClientABC:
    for platform in platforms:
        if platform.type != platform_type:
            continue

        return await platform.from_telegram_id(telegram_id)

    msg = 'Unsupported platform'
    raise ValueError(msg)


async def get_platform_track(
    track_id: str,
    telegram_id: int,
    platform_type: SongLinkPlatformType,
) -> tuple[PlatformClientABC, Track | None]:
    platform = await get_platform_from_telegram_id(telegram_id, platform_type)
    return platform, await platform.get_track(track_id)
