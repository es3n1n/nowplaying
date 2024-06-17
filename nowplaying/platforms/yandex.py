from datetime import datetime
from typing import AsyncIterator

from yandex_music import ClientAsync
from yandex_music.exceptions import YandexMusicError

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError, PlatformTokenInvalidateError
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
        self.app = app
        self.telegram_id = telegram_id

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        queues = await self.app.queues_list()
        if len(queues) == 0:
            return None

        queue = await self.app.queue(queues[0].id)
        track_id = queue.get_current_track()

        track = await track_id.fetch_track_async()
        return await Track.from_yandex_item(track, is_playing=True)

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        queues = await self.app.queues_list()

        is_first: bool = True
        for queue_it in queues:
            queue = await self.app.queue(queue_it.id)
            if not queue:
                continue

            for track_id in queue.tracks:
                track = await track_id.fetch_track_async()
                yield await Track.from_yandex_item(
                    track=track,
                    played_at=datetime.utcnow(),  # unknown :shrug:
                    is_playing=is_first,
                )

                is_first = False

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        result = await self.app.tracks(track_ids=[track_id])
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

        try:
            client = ClientAsync(token)
            await client.init()
        except Exception:
            raise PlatformTokenInvalidateError(platform=self.type, telegram_id=telegram_id)

        return YandexClient(client, telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/ym/'
