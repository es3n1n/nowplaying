from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlencode

from pylast import LastFMNetwork, PlayedTrack, PyLastError, SessionKeyGenerator, _Request

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.LASTFM


class LastfmClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: False,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False
    }

    def __init__(self, net: LastFMNetwork, telegram_id: int):
        self.net = net
        self.telegram_id = telegram_id

        req = _Request(
            self.net,
            'user.getInfo'
        ).execute()

        for k in ['lfm', 'user', 'name']:
            req = req.getElementsByTagName(k)[0]

        self.username = req.firstChild.data
        self.user = self.net.get_user(self.username)

    @rethrow_platform_error(PyLastError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        track = self.user.get_now_playing()
        if track is None:
            return None

        return await Track.from_lastfm_item(track, is_playing=True, played_at=datetime.utcnow())

    @rethrow_platform_error(PyLastError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        if track := await self.get_current_playing_track():
            yield track

        for track in self.user.get_recent_tracks(limit=limit):
            assert isinstance(track, PlayedTrack)
            yield await Track.from_lastfm_item(
                track.track,
                played_at=datetime.utcfromtimestamp(int(track.timestamp))
            )

    async def get_track(self, track_id: str) -> Track | None:
        return None

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
