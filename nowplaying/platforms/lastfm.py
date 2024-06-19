from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlencode

from async_lru import alru_cache
from pylast import LastFMNetwork, PlayedTrack, PyLastError, SessionKeyGenerator
from pylast import Track as LastFMTrack
from pylast import _Request

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..external.lastfm import query_lastfm_external_track_links
from ..external.song_link import get_song_link
from ..models.cached_local_track import CachedLocalTrack
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.LASTFM
_TS_NULL = datetime.utcfromtimestamp(0)


class LastfmClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False
    }

    def __init__(self, net: LastFMNetwork, telegram_id: int):
        self.net = net
        self.telegram_id = telegram_id

        req = _Request(self.net, 'user.getInfo').execute()

        for k in ['lfm', 'user', 'name']:
            req = req.getElementsByTagName(k)[0]

        self.username = req.firstChild.data
        self.user = self.net.get_user(self.username)

    @staticmethod
    @alru_cache(maxsize=16)
    async def query_song_link(url: str) -> str | None:
        for external_url in await query_lastfm_external_track_links(url):
            result = await get_song_link(external_url)
            if result is None:
                continue

            return result

        return None

    @classmethod
    async def parse_track(
            cls,
            track: LastFMTrack,
            played_at: datetime = _TS_NULL,
            is_playing: bool = False
    ) -> Track:
        track_url: str = track.get_url()
        out_track = await Track.from_lastfm_item(
            track=track,
            track_url=track_url,
            track_id=None,
            song_link_url=await cls.query_song_link(track_url),
            played_at=played_at,
            is_playing=is_playing,
        )

        if out_track.song_link is not None:  # otherwise, this track isn't available for a download
            out_track.id = db.cache_local_track(platform=TYPE, url=out_track.url, artist=out_track.artist,
                                                name=out_track.name)

        return out_track

    @rethrow_platform_error(PyLastError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        track = self.user.get_now_playing()
        if track is None:
            return None

        return await self.parse_track(track, is_playing=True, played_at=datetime.utcnow())

    @rethrow_platform_error(PyLastError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        if track := await self.get_current_playing_track():
            yield track

        for track in self.user.get_recent_tracks(limit=limit):
            assert isinstance(track, PlayedTrack)
            yield await self.parse_track(
                track.track,
                played_at=datetime.utcfromtimestamp(int(track.timestamp))
            )

    async def get_track(self, track_id: str) -> Track | None:
        cached_track: CachedLocalTrack | None = db.get_cached_local_track_info(track_id)
        if cached_track is None:
            return None

        track = self.net.get_track(cached_track.artist, cached_track.name)
        return await self.parse_track(track)

    async def add_to_queue(self, track_id: str) -> bool:
        return False

    async def play(self, track_id: str) -> bool:
        return False


class LastfmPlatform(PlatformABC):
    type = TYPE

    @staticmethod
    def _net(session_key: str | None = None, token: str | None = None) -> LastFMNetwork:
        return LastFMNetwork(
            api_key=config.LASTFM_API_KEY,
            api_secret=config.LASTFM_SHARED_SECRET,
            session_key=(session_key or ''),
            token=(token or '')
        )

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        try:
            skg = SessionKeyGenerator(cls._net())
            session_key = skg.get_web_auth_session_key('', auth_code)
        except PyLastError:
            raise PlatformInvalidAuthCodeError(platform=cls.type, telegram_id=telegram_id)

        db.store_user_token(telegram_id, cls.type, session_key)
        return LastfmClient(cls._net(session_key), telegram_id)

    @classmethod
    async def from_telegram_id(cls, telegram_id: int) -> PlatformClientABC:
        token_data = db.get_user_token(telegram_id, cls.type)
        assert token_data is not None

        return LastfmClient(
            cls._net(
                session_key=token_data,
            ),
            telegram_id
        )

    async def get_authorization_url(self, state: str) -> str:
        kw = {
            'api_key': config.LASTFM_API_KEY,
            'cb': config.LASTFM_REDIRECT_URL + '?' + urlencode({
                'state': state
            })
        }
        return f'https://www.last.fm/api/auth/?{urlencode(kw)}'
