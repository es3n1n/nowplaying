from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from re import DOTALL, compile, findall, search

from async_lru import alru_cache
from httpx import AsyncClient, Response
from orjson import loads

from ..core.config import config


client = AsyncClient(headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0'
}, follow_redirects=True)

PLAY_LINKS_REGEX = compile(r'<ul\sclass="play-this-track-playlinks">(.*?)</ul>', DOTALL)
HREF_URL_REGEX = compile(r'href="(https://.{1,100})"')


@alru_cache(maxsize=32)
async def query_lastfm_external_track_links(track: str) -> list[str]:
    response = await client.get(track)
    if response.status_code != 200:
        raise ValueError(f'Got status code {response.status_code}')

    container = search(PLAY_LINKS_REGEX, response.text)
    if container is None:
        return []

    result = list(set(findall(HREF_URL_REGEX, container.group(1))))
    return result


class LastFMError(Exception):
    pass


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


class LastFMClient:
    def __init__(self, session_key: str | None = None, token: str | None = None):
        self.api_key = config.LASTFM_API_KEY
        self.api_secret = config.LASTFM_SHARED_SECRET
        self.session_key = session_key
        self.token = token
        self.client = AsyncClient(
            headers={
                'User-Agent': 'playinnowbot'
            },
        )
        self.base_url = 'https://ws.audioscrobbler.com/2.0/'

    def _get_signature(self, params: dict[str, str]):
        string = ''
        for name in sorted(params.keys()):
            string += f'{name}{params[name]}'

        string += self.api_secret

        h = md5()
        h.update(string.encode('utf-8'))
        return h.hexdigest()

    def _build_query(self, method: str, **kwargs) -> dict[str, str]:
        kwargs['method'] = method
        kwargs['api_key'] = self.api_key
        if self.session_key is not None:
            kwargs['sk'] = self.session_key
        kwargs['api_sig'] = self._get_signature(kwargs)
        kwargs['format'] = 'json'
        return kwargs

    @staticmethod
    def _ensure_response(r: Response) -> None:
        if r.status_code != 200:
            raise LastFMError(f'status {r.status_code} != 200 {r.text}')

    async def get_session_key(self) -> str:
        if self.token is None:
            raise LastFMError()

        r = await self.client.get(
            self.base_url,
            params=self._build_query(
                'auth.getSession',
                token=self.token
            )
        )
        self._ensure_response(r)

        data = loads(r.content)
        session_key: str | None = data.get('session', {}).get('key', None)
        if session_key is None:
            raise LastFMError()

        return session_key

    async def get_username(self) -> str:
        if self.session_key is None:
            raise LastFMError()
        r = await self.client.get(self.base_url, params=self._build_query('user.getInfo'))
        self._ensure_response(r)
        data = loads(r.content)
        return data['user']['name']

    async def get_recent_tracks(self, limit: int) -> list[LastFMPlayedTrack]:
        if self.session_key is None:
            raise LastFMError()
        r = await self.client.get(
            self.base_url,
            params=self._build_query(
                'user.getRecentTracks',
                user=await self.get_username(),
                limit=limit,
            )
        )
        self._ensure_response(r)
        data = loads(r.content)

        result: list[LastFMPlayedTrack] = list()
        for track in data.get('recenttracks', {}).get('track', []):
            is_now_playing: bool = track.get('@attr', {}).get('nowplaying', False)

            played_ts: str | None = track.get('date', {}).get('uts', None)
            played_at = datetime.utcnow() if played_ts is None else datetime.utcfromtimestamp(int(played_ts))

            result.append(LastFMPlayedTrack(
                is_now_playing=is_now_playing,
                track=LastFMTrack(
                    url=track['url'],
                    artist=track['artist']['#text'],
                    name=track['name']
                ),
                playback_date=played_at
            ))

        return result
