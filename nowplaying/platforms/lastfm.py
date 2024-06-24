from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urlencode

from async_lru import alru_cache

from ..core.config import config
from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..exceptions.platforms import PlatformInvalidAuthCodeError
from ..external.lastfm import LastFMClient, LastFMError, LastFMTrack, query_lastfm_external_track_links
from ..external.song_link import get_song_link
from ..models.cached_local_track import CachedLocalTrack
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track
from ..util.exceptions import rethrow_platform_error
from .abc import PlatformABC, PlatformClientABC


TYPE = SongLinkPlatformType.LASTFM
_TS_NULL = datetime.utcfromtimestamp(0)


@alru_cache()
async def _query_song_link(url: str) -> str | None:
    for external_url in await query_lastfm_external_track_links(url):
        song_link = await get_song_link(external_url)
        if song_link is None:
            continue

        return song_link

    return None


class LastfmClient(PlatformClientABC):
    features = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False,
    }

    def __init__(self, net: LastFMClient, telegram_id: int):
        self.net = net
        self.telegram_id = telegram_id

    @rethrow_platform_error(LastFMError, TYPE)
    async def get_current_playing_track(self) -> Track | None:
        raise NotImplementedError()

    @rethrow_platform_error(LastFMError, TYPE)
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        # Limit is without the currently playing track, no need to do +1
        for track in await self.net.get_recent_tracks(limit=limit):
            yield await self._parse_track(
                track.track,
                played_at=track.playback_date,
                is_playing=track.is_now_playing,
            )

    @rethrow_platform_error(LastFMError, TYPE)
    async def get_track(self, track_id: str) -> Track | None:
        cached_track: CachedLocalTrack | None = await db.get_cached_local_track_info(track_id)
        if cached_track is None:
            return None

        return await self._parse_track(LastFMTrack(
            url=cached_track.url,
            artist=cached_track.artist,
            name=cached_track.name,
        ))

    async def add_to_queue(self, track_id: str) -> bool:
        return False

    async def play(self, track_id: str) -> bool:
        return False

    @classmethod
    async def _parse_track(
        cls,
        track: LastFMTrack,
        played_at: datetime = _TS_NULL,
        is_playing: bool = False,
    ) -> Track:
        out_track = await Track.from_lastfm_item(
            track=track,
            track_id=None,
            song_link_url=await _query_song_link(track.url),
            played_at=played_at,
            is_playing=is_playing,
        )

        if out_track.song_link is not None:  # otherwise, this track isn't available for a download
            out_track.id = await db.cache_local_track(
                platform=TYPE, url=out_track.url, artist=out_track.artist, name=out_track.name,
            )

        return out_track


class LastfmPlatform(PlatformABC):
    type = TYPE

    @classmethod
    async def from_auth_callback(cls, telegram_id: int, auth_code: str) -> PlatformClientABC:
        cl = LastFMClient(token=auth_code)
        try:
            session_key = await cl.get_session_key()
        except LastFMError:
            raise PlatformInvalidAuthCodeError(platform=cls.type, telegram_id=telegram_id)

        await db.store_user_token(telegram_id, cls.type, session_key)
        return LastfmClient(LastFMClient(session_key), telegram_id)

    @classmethod
    async def from_telegram_id(cls, telegram_id: int) -> PlatformClientABC:
        session_key = await db.get_user_token(telegram_id, cls.type)
        if session_key is None:
            raise ValueError('session is None')
        return LastfmClient(LastFMClient(session_key), telegram_id)

    async def get_authorization_url(self, state: str) -> str:
        state_query = urlencode({
            'state': state,
        })
        redirect_url = config.redirect_url_for_ext_svc('lastfm')
        query = urlencode({
            'api_key': config.LASTFM_API_KEY,
            'cb': f'{redirect_url}?{state_query}',
        })
        return f'https://www.last.fm/api/auth/?{query}'
