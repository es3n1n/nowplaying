from datetime import datetime, timedelta
from typing import AsyncIterator

from yandex_music import ClientAsync
from yandex_music.exceptions import YandexMusicError

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..external.yandex_yaynison import Yaynison, YaynisonException
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.YANDEX


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

    async def get_app(self) -> ClientAsync:
        if not self._initialized_app:
            # There is no need to initialize this thing for our needs
            # await self._app.init()
            self._initialized_app = True
        return self._app

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        raise ValueError('not implemented')

    @rethrow_platform_error(YandexMusicError, TYPE)
    @rethrow_platform_error(YaynisonException, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        limit += 1  # the limit does not include currently playing track
        playable_items = await self._yaynison.one_shot_playable_items()
        ids = [item.playable_id for item in playable_items[:limit]]

        app = await self.get_app()
        tracks = await app.tracks(track_ids=ids)
        cur_time = datetime.utcnow()

        for i, track in enumerate(tracks):
            if not track:
                continue

            yield await Track.from_yandex_item(
                track,
                played_at=cur_time - timedelta(minutes=i),  # used for sorting
            )

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        app = await self.get_app()
        result = await app.tracks(track_ids=[track_id])
        if len(result) == 0:
            return None

        return await Track.from_yandex_item(result[0])

    async def add_to_queue(self, track_id: str) -> bool:
        return True

    async def play(self, track_id: str) -> bool:
        return True


class YandexPlatform(PlatformABC):
    type = SongLinkPlatformType.YANDEX

    def __init__(self):
        pass

    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        try:
            client = ClientAsync(auth_code)
            await client.init()
        except Exception:
            raise PlatformInvalidAuthCodeError(platform=self.type, telegram_id=telegram_id)

        db.store_user_token(telegram_id, self.type, auth_code)
        return YandexClient(client, telegram_id)

    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        token = db.get_user_token(telegram_id, self.type)
        assert token is not None
        return YandexClient(ClientAsync(token), telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/ym/'
