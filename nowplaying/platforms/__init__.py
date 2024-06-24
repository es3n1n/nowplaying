from typing import Tuple

from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
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

    raise ValueError('Unsupported platform')


async def get_platform_authorization_url(state: str, platform_type: SongLinkPlatformType) -> str:
    for platform in platforms:
        if platform.type != platform_type:
            continue

        return await platform.get_authorization_url(state)

    raise ValueError('Unsupported platform')


async def get_platform_track(
    track_id: str,
    telegram_id: int,
    platform_type: SongLinkPlatformType,
) -> Tuple[PlatformClientABC, Track | None]:
    platform = await get_platform_from_telegram_id(telegram_id, platform_type)
    return platform, await platform.get_track(track_id)
