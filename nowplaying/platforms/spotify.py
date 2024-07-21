from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlencode

import orjson

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError, PlatformTokenInvalidateError
from ..external.spotify import Spotify, SpotifyCacheHandlerABC, SpotifyError
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from ..util.time import UTC_TZ
from .abc import PlatformABC, PlatformClientABC, auto_memorize_tracks


TYPE = SongLinkPlatformType.SPOTIFY
SCOPE = 'user-read-currently-playing,user-read-recently-played,streaming'
REDIRECT_URI = config.redirect_url_for_ext_svc('spotify')


def _to_uri(track_id: str) -> str:
    return f'spotify:track:{track_id}'


class SpotifyClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: True,
        PlatformFeature.PLAY: True,
    }

    def __init__(self, spotify_app: Spotify, telegram_id: int):
        self.spotify_app = spotify_app
        self.telegram_id = telegram_id

    @rethrow_platform_error(SpotifyError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        track = await self.spotify_app.get_current_user_playing_track()
        if track is None:
            return None

        return await Track.from_spotify_item(track['item'], datetime.utcnow(), is_playing=True)

    @rethrow_platform_error(SpotifyError, TYPE)
    @auto_memorize_tracks
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        current_playing = await self.get_current_playing_track()
        if current_playing:
            yield current_playing

        history = await self.spotify_app.get_current_user_recently_played(limit=limit)
        for history_item in history['items']:
            yield await Track.from_spotify_item(
                history_item['track'],
                datetime.fromisoformat(history_item['played_at']).replace(tzinfo=UTC_TZ),
            )

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
        cached_token = await db.get_user_token(self.telegram_id, TYPE)
        return orjson.loads(cached_token) if cached_token is not None else None

    async def save_token_to_cache(self, token_info: dict) -> None:
        token_info_str = orjson.dumps(token_info).decode()
        await db.store_user_token(self.telegram_id, TYPE, token_info_str)


class SpotifyPlatform(PlatformABC):
    type = SongLinkPlatformType.SPOTIFY

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        client = cls._get_client(telegram_id)
        try:
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
        query = urlencode({
            'client_id': config.SPOTIFY_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'state': state,
            'scope': SCOPE,
        })
        return f'https://accounts.spotify.com/authorize?{query}'

    @classmethod
    def _get_client(cls, telegram_id: int) -> Spotify:
        return Spotify(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_handler=SpotifyCacheHandler(telegram_id),
        )
