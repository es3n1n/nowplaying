from datetime import datetime, timedelta
from typing import AsyncIterator

from yandex_music import ClientAsync
from yandex_music import Track as YandexTrack
from yandex_music.exceptions import TimedOutError, YandexMusicError

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..external.yaynison import Yaynison, YaynisonError
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC, auto_memorize_tracks


TYPE = SongLinkPlatformType.YANDEX
NUM_TIMEOUT_RETRIES = 5


class YandexClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False,
    }

    def __init__(self, app: ClientAsync, telegram_id: int):
        self._app = app
        self._yaynison = Yaynison(app.token)

        self.telegram_id = telegram_id
        self._initialized_app: bool = False

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        raise ValueError('not implemented')

    @rethrow_platform_error(YandexMusicError, TYPE)
    @rethrow_platform_error(YaynisonError, TYPE)
    @auto_memorize_tracks
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:  # noqa: WPS463
        playable_items = await self._yaynison.one_shot_playable_items()
        if not playable_items:
            return

        tracks: list[YandexTrack] = []

        for _ in range(NUM_TIMEOUT_RETRIES):
            try:
                tracks = await self._app.tracks(
                    track_ids=[playable.playable_id for playable in playable_items[:limit + 1]],
                )
            except TimedOutError:
                continue

            break

        cur_time = datetime.utcnow()

        for index, track in enumerate(tracks):
            if not track:
                continue

            yield await Track.from_yandex_item(
                track,
                played_at=cur_time - timedelta(minutes=index),  # used for sorting
            )

    async def add_to_queue(self, track_id: str) -> bool:
        return True

    async def play(self, track_id: str) -> bool:
        return True


class YandexPlatform(PlatformABC):
    type = SongLinkPlatformType.YANDEX

    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        client = ClientAsync(auth_code)
        try:
            await client.init()
        except Exception:
            raise PlatformInvalidAuthCodeError(platform=self.type, telegram_id=telegram_id)

        await db.store_user_token(telegram_id, self.type, auth_code)
        return YandexClient(client, telegram_id)

    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        token = await db.get_user_token(telegram_id, self.type)
        if token is None:
            raise ValueError('token is none')
        return YandexClient(ClientAsync(token), telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/ym/'
