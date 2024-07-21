from datetime import datetime, timedelta
from typing import AsyncIterator
from urllib.parse import quote

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..external.apple import AppleMusicError, AppleMusicWrapper, AppleMusicWrapperClient
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC, auto_memorize_tracks


TYPE = SongLinkPlatformType.APPLE


class AppleClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False,
    }

    def __init__(self, app: AppleMusicWrapperClient, telegram_id: int):
        self.app = app
        self.telegram_id = telegram_id

    async def get_current_playing_track(self) -> Track | None:
        raise NotImplementedError()

    @rethrow_platform_error(AppleMusicError, TYPE)
    @auto_memorize_tracks
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        cur_time = datetime.utcnow()

        # Add 1 to the limit because the currently playing track is not counted,
        # but Apple Music includes it in the recently played tracks.
        for index, track in enumerate(await self.app.recently_played(limit=limit + 1)):
            yield await Track.from_apple_item(
                track,
                played_at=cur_time - timedelta(minutes=index),
            )

    async def add_to_queue(self, track_id: str) -> bool:
        return True

    async def play(self, track_id: str) -> bool:
        return True

    async def is_alive(self) -> bool:
        try:
            await self.app.recently_played(1)
        except AppleMusicError:
            return False

        return self.telegram_id != 0


class ApplePlatform(PlatformABC):
    type = TYPE

    def __init__(self):
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
            raise ValueError('token is none')
        return AppleClient(self.app.with_media_token(token), telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/apple/?state={quote(state)}'
