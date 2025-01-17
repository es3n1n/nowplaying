from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from types import MappingProxyType

from yandex_music.exceptions import TimedOutError, YandexMusicError

from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.exceptions.platforms import PlatformInvalidAuthCodeError
from nowplaying.external.yandex import ClientAsync
from nowplaying.external.ynison.ynison_grpc import Ynison, YnisonClientSideError
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track
from nowplaying.platforms.abc import PlatformABC, PlatformClientABC, PlatformClientSideError
from nowplaying.util.exceptions import rethrow_platform_error
from nowplaying.util.time import UTC_TZ


TYPE = SongLinkPlatformType.YANDEX


class YandexClient(PlatformClientABC):
    features: MappingProxyType[PlatformFeature, bool] = MappingProxyType(
        {
            PlatformFeature.TRACK_GETTERS: True,
            PlatformFeature.ADD_TO_QUEUE: True,
            PlatformFeature.PLAY: True,
        }
    )
    media_notice = (
        'Please note that buttons below might not work properly with desktop app,'
        ' and slightly lag with web app (you may need to refresh page to reload the queue)'
    )

    def __init__(self, app: ClientAsync, telegram_id: int) -> None:
        self._app = app
        self._ynison = Ynison(app.token)

        self.telegram_id = telegram_id
        self._initialized_app: bool = False

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        raise NotImplementedError

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        playable_items = await self._ynison.get_playable_items(from_current_to_prev=True)
        if not playable_items:
            return

        try:
            tracks = await self._app.tracks(
                track_ids=[playable.playable_id for playable in playable_items[: limit + 1]],
            )
        except TimedOutError:
            # :shrug:
            return

        cur_time = datetime.now(tz=UTC_TZ)

        for index, track in enumerate(tracks):
            if not track:
                continue

            # Skip local tracks, UGC probably stands for "User Generated Content"
            if track.track_source == 'UGC':
                continue

            yield await Track.from_yandex_item(
                track,
                played_at=cur_time - timedelta(minutes=index),  # used for sorting
            )

    @rethrow_platform_error(YandexMusicError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        tracks = await self._app.tracks(track_ids=[track_id])
        if not tracks:
            return None

        return await Track.from_yandex_item(tracks[0])

    async def add_to_queue(self, track_id: str) -> None:
        try:
            await self._ynison.add_to_queue(track_id)
        except YnisonClientSideError as err:
            raise PlatformClientSideError(str(err)) from err

    async def play(self, track_id: str) -> None:
        try:
            await self._ynison.play_track(track_id, keep_queue=True)
        except YnisonClientSideError as err:
            raise PlatformClientSideError(str(err)) from err


class YandexPlatform(PlatformABC):
    type = SongLinkPlatformType.YANDEX

    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        client = ClientAsync(auth_code)
        try:
            await client.init()
        except Exception as err:
            raise PlatformInvalidAuthCodeError(platform=self.type, telegram_id=telegram_id) from err

        await db.store_user_token(telegram_id, self.type, auth_code)
        return YandexClient(client, telegram_id)

    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        token = await db.get_user_token(telegram_id, self.type)
        if token is None:
            err_msg = 'token is none'
            raise ValueError(err_msg)
        return YandexClient(ClientAsync(token), telegram_id)

    async def get_authorization_url(self, _: str) -> str:
        return f'{config.WEB_SERVER_PUBLIC_ENDPOINT}/ym/'
