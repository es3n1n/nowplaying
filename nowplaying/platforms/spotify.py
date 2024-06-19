from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlencode

from orjson import dumps, loads

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError, PlatformTokenInvalidateError
from ..external.spotify import Spotify, SpotifyCacheHandlerABC, SpotifyError
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from ..util.tz import UTC_TZ
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.SPOTIFY
SCOPE = 'user-read-currently-playing,user-read-recently-played,streaming'


def _to_uri(track_id: str) -> str:
    return f'spotify:track:{track_id}'


class SpotifyClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: True,
        PlatformFeature.PLAY: True
    }

    def __init__(self, spotify_app: Spotify, telegram_id: int):
        self.spotify_app = spotify_app
        self.telegram_id = telegram_id

    @rethrow_platform_error(SpotifyError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        track = await self.spotify_app.get_current_user_playing_track()
        if track['item'] is None:
            return None

        return await Track.from_spotify_item(track['item'], datetime.utcnow(), is_playing=True)

    @rethrow_platform_error(SpotifyError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        if track := await self.get_current_playing_track():
            yield track

        history = await self.spotify_app.get_current_user_recently_played(limit=limit)
        for item in history['items']:
            yield await Track.from_spotify_item(
                item['track'],
                datetime.fromisoformat(item['played_at']).replace(tzinfo=UTC_TZ)
            )

    @rethrow_platform_error(SpotifyError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        result = await self.spotify_app.get_track(track_id)
        if result is None:
            return None

        return await Track.from_spotify_item(result)

    @rethrow_platform_error(SpotifyError, TYPE)
    async def add_to_queue(self, track_id: str) -> bool:
        await self.spotify_app.add_to_queue(_to_uri(track_id))
        return True

    @rethrow_platform_error(SpotifyError, TYPE)
    async def play(self, track_id: str) -> bool:
        await self.spotify_app.start_playback(uris=[_to_uri(track_id)])
        return True


class SpotifyCacheHandler(SpotifyCacheHandlerABC):
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id

    async def get_cached_token(self) -> dict | None:
        result = await db.get_user_token(self.telegram_id, TYPE)
        return loads(result) if result is not None else None

    async def save_token_to_cache(self, token_info: dict) -> None:
        token_info_str = dumps(token_info).decode()
        await db.store_user_token(self.telegram_id, TYPE, token_info_str)


class SpotifyPlatform(PlatformABC):
    type = SongLinkPlatformType.SPOTIFY

    @staticmethod
    def _get_client(telegram_id: int) -> Spotify:
        return Spotify(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URL,
            scope=SCOPE,
            cache_handler=SpotifyCacheHandler(telegram_id),
        )

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        try:
            client = cls._get_client(telegram_id)
            await client.get_access_token(auth_code)
        except SpotifyError:
            raise PlatformInvalidAuthCodeError(platform=cls.type, telegram_id=telegram_id)

        return SpotifyClient(client, telegram_id)

    @classmethod
    async def from_telegram_id(cls, telegram_id: int) -> PlatformClientABC:
        client = cls._get_client(telegram_id)
        try:
            await client.gather_token()
        except SpotifyError:
            raise PlatformTokenInvalidateError(platform=TYPE, telegram_id=telegram_id)

        return SpotifyClient(client, telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        kw = {
            'client_id': config.SPOTIFY_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': config.SPOTIFY_REDIRECT_URL,
            'state': state,
            'scope': SCOPE,
        }
        return f'https://accounts.spotify.com/authorize?{urlencode(kw)}'
