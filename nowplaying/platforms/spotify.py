from datetime import datetime
from typing import AsyncIterator

from orjson import dumps, loads
from spotipy import CacheHandler as _CacheHandler
from spotipy import Spotify as _Spotify
from spotipy import SpotifyException
from spotipy import SpotifyOAuth as _SpotifyOAuth
from spotipy import SpotifyOauthError

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from ..util.tz import UTC_TZ
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.SPOTIFY


def _to_uri(track_id: str) -> str:
    return f'spotify:track:{track_id}'


class SpotifyClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: True,
        PlatformFeature.PLAY: True
    }

    def __init__(self, spotify_app: _Spotify, telegram_id: int):
        self.spotify_app = spotify_app
        self.telegram_id = telegram_id

    @rethrow_platform_error(SpotifyException, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        track = self.spotify_app.current_user_playing_track()
        if track['item'] is None:
            return None

        return await Track.from_spotify_item(track['item'], datetime.utcnow(), is_playing=True)

    @rethrow_platform_error(SpotifyException, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        if track := await self.get_current_playing_track():
            yield track

        history = self.spotify_app.current_user_recently_played(limit=limit)
        for item in history['items']:
            yield await Track.from_spotify_item(
                item['track'],
                datetime.fromisoformat(item['played_at']).replace(tzinfo=UTC_TZ)
            )

    @rethrow_platform_error(SpotifyException, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        try:
            return await Track.from_spotify_item(self.spotify_app.track(track_id))
        except SpotifyException:
            return None

    @rethrow_platform_error(SpotifyException, TYPE)
    async def add_to_queue(self, track_id: str) -> bool:
        self.spotify_app.add_to_queue(_to_uri(track_id))
        return True

    @rethrow_platform_error(SpotifyException, TYPE)
    async def play(self, track_id: str) -> bool:
        self.spotify_app.start_playback(uris=[_to_uri(track_id)])
        return True


class SpotifyCacheHandler(_CacheHandler):
    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id

    def get_cached_token(self) -> dict | None:
        result = db.get_user_token(self.telegram_id, TYPE)
        return loads(result) if result is not None else None

    def save_token_to_cache(self, token_info: dict) -> None:
        token_info_str = dumps(token_info).decode()
        db.store_user_token(self.telegram_id, TYPE, token_info_str)


class SpotifyPlatform(PlatformABC):
    type = SongLinkPlatformType.SPOTIFY

    def __init__(self):
        self.general_purpose_manager = self._get_manager()

    @staticmethod
    def _get_manager(telegram_id: int | None = None) -> _SpotifyOAuth:
        cache_handler: SpotifyCacheHandler | None = None
        if telegram_id is not None:
            cache_handler = SpotifyCacheHandler(telegram_id)

        return _SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URL,
            open_browser=False,
            scope='user-read-currently-playing,user-read-recently-played,streaming',
            cache_handler=cache_handler,
        )

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        try:
            manager = cls._get_manager(telegram_id)
            manager.get_access_token(auth_code)
        except SpotifyOauthError:
            raise PlatformInvalidAuthCodeError(platform=cls.type, telegram_id=telegram_id)

        return SpotifyClient(
            _Spotify(auth_manager=manager), telegram_id
        )

    @classmethod
    async def from_telegram_id(cls, telegram_id: int) -> PlatformClientABC:
        return SpotifyClient(
            _Spotify(auth_manager=cls._get_manager(telegram_id)), telegram_id
        )

    async def get_authorization_url(self, state: str) -> str:
        return self.general_purpose_manager.get_authorize_url(
            state=state
        )
