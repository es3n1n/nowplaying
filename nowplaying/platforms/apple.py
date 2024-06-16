from typing import AsyncIterator

from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..external.apple import AppleMusicWrapper, AppleMusicWrapperClient
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from .abc import PlatformABC, PlatformClientABC


class AppleClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: True,
        PlatformFeature.PLAY: True
    }

    def __init__(self, app: AppleMusicWrapperClient):
        self.app = app

    async def get_current_playing_track(self) -> Track | None:
        return None

    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        if track := await self.get_current_playing_track():
            yield track

        # history = self.spotify_app.current_user_recently_played(limit=limit)
        # for item in history['items']:
        #     yield await Track.from_spotify_item(
        #         item['track'],
        #         datetime.fromisoformat(item['played_at']).replace(tzinfo=UTC_TZ)
        #     )

    async def get_track(self, track_id: str) -> Track | None:
        return None

    async def add_to_queue(self, track_id: str) -> bool:
        return True

    async def play(self, track_id: str) -> bool:
        return True

    async def is_alive(self) -> bool:
        return True


class ApplePlatform(PlatformABC):
    type = SongLinkPlatformType.APPLE_MUSIC

    def __init__(self):
        self.app = AppleMusicWrapper()

    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        client = AppleClient(self.app.with_media_token(auth_code))

        if not await client.is_alive():
            raise ValueError()

        db.store_user_token(telegram_id, SongLinkPlatformType.APPLE_MUSIC, auth_code)
        return client

    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        token = db.get_user_token(telegram_id, SongLinkPlatformType.APPLE_MUSIC)
        assert token is not None
        return AppleClient(self.app.with_media_token(token))

    async def get_authorization_url(self, state: str) -> str:
        return 'https://google.com/'
