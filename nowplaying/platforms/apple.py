from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from types import MappingProxyType
from urllib.parse import quote

from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.exceptions.platforms import PlatformInvalidAuthCodeError
from nowplaying.external.apple import AppleMusicError, AppleMusicWrapper, AppleMusicWrapperClient
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track
from nowplaying.platforms.abc import PlatformABC, PlatformClientABC
from nowplaying.util.exceptions import rethrow_platform_error
from nowplaying.util.logger import logger
from nowplaying.util.time import UTC_TZ


TYPE = SongLinkPlatformType.APPLE


class AppleClient(PlatformClientABC):
    features: MappingProxyType[PlatformFeature, bool] = MappingProxyType(
        {
            PlatformFeature.TRACK_GETTERS: True,
        }
    )

    def __init__(self, app: AppleMusicWrapperClient, telegram_id: int) -> None:
        self.app = app
        self.telegram_id = telegram_id

    async def get_current_playing_track(self) -> Track | None:
        raise NotImplementedError

    @rethrow_platform_error(AppleMusicError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        cur_time = datetime.now(tz=UTC_TZ)

        # Add 1 to the limit because the currently playing track is not counted,
        # but Apple Music includes it in the recently played tracks.
        for index, track in enumerate(await self.app.recently_played(limit=limit + 1)):
            if track.is_local:
                continue

            yield await Track.from_apple_item(
                track,
                played_at=cur_time - timedelta(minutes=index),
            )

    @rethrow_platform_error(AppleMusicError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        track_info = await self.app.get_track(track_id)
        if track_info is None:
            return None

        return await Track.from_apple_item(track_info)

    async def add_to_queue(self, _: str) -> None:
        raise NotImplementedError

    async def play(self, _: str) -> None:
        raise NotImplementedError

    async def like(self, _: str) -> None:
        raise NotImplementedError

    async def is_alive(self) -> bool:
        try:
            await self.app.recently_played(1)
        except AppleMusicError as exc:
            logger.opt(exception=exc).warning('Apple music client is not alive')
            return False

        return self.telegram_id != 0


class ApplePlatform(PlatformABC):
    type = TYPE

    def __init__(self) -> None:
        self.app = AppleMusicWrapper()

    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        client = AppleClient(self.app.with_media_token(auth_code), telegram_id)

        if not await client.is_alive():
            raise PlatformInvalidAuthCodeError(platform=self.type, telegram_id=telegram_id)

        await db.store_user_token(telegram_id, TYPE, auth_code)
        return client

    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        token = await db.get_user_token(telegram_id, TYPE)
        if token is None:
            msg = 'token is none'
            raise ValueError(msg)
        return AppleClient(self.app.with_media_token(token), telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/apple/?state={quote(state)}'
