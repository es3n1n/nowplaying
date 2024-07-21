from typing import Tuple

from ..core.database import db
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


async def get_platform_track(
    track_id: str,
    telegram_id: int,
    platform_type: SongLinkPlatformType,
) -> Tuple[PlatformClientABC, Track | None]:
    platform = await get_platform_from_telegram_id(telegram_id, platform_type)
    cached_track = await db.get_cached_local_track_info(track_id, platform_type)

    if cached_track is None:
        return platform, None

    return platform, await Track.from_cached(cached_track)
