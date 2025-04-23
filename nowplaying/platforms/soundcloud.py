from collections.abc import AsyncIterator
from datetime import datetime
from types import MappingProxyType

from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformInvalidAuthCodeError
from nowplaying.external.soundcloud import SoundCloudError, SoundCloudWrapper
from nowplaying.models.track import Track
from nowplaying.platforms import PlatformABC, PlatformClientABC
from nowplaying.util.exceptions import rethrow_platform_error
from nowplaying.util.time import UTC_TZ


TYPE = SongLinkPlatformType.SOUNDCLOUD


class SoundCloudClient(PlatformClientABC):
    features: MappingProxyType[PlatformFeature, bool] = MappingProxyType(
        {
            PlatformFeature.TRACK_GETTERS: True,
            PlatformFeature.ADD_TO_QUEUE: False,
            PlatformFeature.PLAY: False,
        }
    )

    def __init__(self, wrapper: SoundCloudWrapper, telegram_id: int) -> None:
        self.wrapper = wrapper
        self.telegram_id = telegram_id

    @rethrow_platform_error(SoundCloudError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        raise NotImplementedError

    @rethrow_platform_error(SoundCloudError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        # Limit is without the currently playing track, that's why we have to do +1
        for track in await self.wrapper.get_play_history(limit=limit + 1):
            yield await Track.from_soundcloud_item(
                track=track.track,
                played_at=datetime.fromtimestamp(track.played_at, tz=UTC_TZ),
            )

    @rethrow_platform_error(SoundCloudError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        result = await self.wrapper.get_track(track_id=int(track_id))
        if not result:
            return None

        return await Track.from_soundcloud_item(result)

    async def add_to_queue(self, _: str) -> None:
        raise NotImplementedError

    async def play(self, _: str) -> None:
        raise NotImplementedError


class SoundCloudPlatform(PlatformABC):
    type = TYPE

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        wrapper = SoundCloudWrapper(oauth_token=auth_code)
        try:
            await wrapper.get_play_history(limit=1)
        except Exception as err:
            raise PlatformInvalidAuthCodeError(platform=cls.type, telegram_id=telegram_id) from err

        await db.store_user_token(telegram_id, cls.type, auth_code)
        return SoundCloudClient(wrapper, telegram_id)

    @classmethod
    async def from_telegram_id(cls, telegram_id: int) -> PlatformClientABC:
        oauth_token = await db.get_user_token(telegram_id, cls.type)
        if oauth_token is None:
            msg = 'oauth_token is None'
            raise ValueError(msg)
        return SoundCloudClient(SoundCloudWrapper(oauth_token), telegram_id)

    async def get_authorization_url(self, _: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/sc/'
