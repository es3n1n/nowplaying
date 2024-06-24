from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from re import DOTALL
from re import compile as re_compile
from re import findall, search

import orjson
from async_lru import alru_cache
from httpx import AsyncClient, Response

from ..core.config import config
from ..util.http import STATUS_OK


client = AsyncClient(
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    },
    follow_redirects=True,
)

PLAY_LINKS_REGEX = re_compile(r'<ul\sclass="play-this-track-playlinks">(.*?)</ul>', DOTALL)
HREF_URL_REGEX = re_compile('href="(https://.{1,100})"')


@alru_cache()
async def query_lastfm_external_track_links(track: str) -> list[str]:
    response = await client.get(track)
    if response.status_code != STATUS_OK:
        raise ValueError(f'Got status code {response.status_code}')

    container = search(PLAY_LINKS_REGEX, response.text)
    if container is None:
        return []

    return list(set(findall(HREF_URL_REGEX, container.group(1))))


class LastFMError(Exception):
    """LastFM error base class."""


@dataclass
class LastFMTrack:
    url: str
    artist: str
    name: str


@dataclass
class LastFMPlayedTrack:
    is_now_playing: bool
    track: LastFMTrack
    playback_date: datetime


def _ensure_response(response: Response) -> None:
    if response.status_code != STATUS_OK:
        raise LastFMError(f'status {response.status_code} != 200 {response.text}')


class LastFMClient:
    def __init__(self, session_key: str | None = None, token: str | None = None):
        self.api_key = config.LASTFM_API_KEY
        self.api_secret = config.LASTFM_SHARED_SECRET
        self.session_key = session_key
        self.token = token
        self.client = AsyncClient(
            headers={
                'User-Agent': 'playinnowbot',
            },
        )
        self.base_url = 'https://ws.audioscrobbler.com/2.0/'

    async def get_session_key(self) -> str:  # noqa: WPS615
        if self.token is None:
            raise LastFMError()

        response = await self.client.get(
            self.base_url,
            params=self._build_query(
                'auth.getSession',
                token=self.token,
            ),
        )
        _ensure_response(response)

        session_data = orjson.loads(response.content)
        session_key: str | None = session_data.get('session', {}).get('key', None)
        if session_key is None:
            raise LastFMError()

        return session_key

    async def get_username(self) -> str:
        if self.session_key is None:
            raise LastFMError()
        response = await self.client.get(self.base_url, params=self._build_query('user.getInfo'))
        _ensure_response(response)
        user_data = orjson.loads(response.content)
        return user_data['user']['name']

    async def get_recent_tracks(self, limit: int) -> list[LastFMPlayedTrack]:
        if self.session_key is None:
            raise LastFMError()
        response = await self.client.get(
            self.base_url,
            params=self._build_query(
                'user.getRecentTracks',
                user=await self.get_username(),
                limit=limit,
            ),
        )
        _ensure_response(response)
        response_data = orjson.loads(response.content)

        played_tracks: list[LastFMPlayedTrack] = []
        for track in response_data.get('recenttracks', {}).get('track', []):
            is_now_playing: bool = track.get('@attr', {}).get('nowplaying', False)

            played_ts: str | None = track.get('date', {}).get('uts', None)
            played_at = datetime.utcnow() if played_ts is None else datetime.utcfromtimestamp(int(played_ts))

            played_tracks.append(LastFMPlayedTrack(
                is_now_playing=is_now_playing,
                track=LastFMTrack(
                    url=track['url'],
                    artist=track['artist']['#text'],
                    name=track['name'],
                ),
                playback_date=played_at,
            ))

        return played_tracks

    def _get_signature(self, query_params: dict[str, str]):
        string = ''
        for name in sorted(query_params.keys()):  # noqa: WPS519
            string += f'{name}{query_params[name]}'  # noqa: WPS336

        string += self.api_secret

        hashed = md5(usedforsecurity=False)
        hashed.update(string.encode('utf-8'))
        return hashed.hexdigest()

    def _build_query(self, method: str, **kwargs) -> dict[str, str]:
        kwargs['method'] = method
        kwargs['api_key'] = self.api_key
        if self.session_key is not None:
            kwargs['sk'] = self.session_key
        kwargs['api_sig'] = self._get_signature(kwargs)
        kwargs['format'] = 'json'
        return kwargs
