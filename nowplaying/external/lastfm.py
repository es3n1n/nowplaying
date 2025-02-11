from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from html import unescape
from re import DOTALL, findall, search
from re import compile as re_compile
from typing import NoReturn

import orjson
from async_lru import alru_cache
from httpx import AsyncClient, AsyncHTTPTransport, HTTPError, Response, Timeout

from nowplaying.core.config import config
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTemporarilyUnavailableError
from nowplaying.util.http import STATUS_OK, is_serverside_error
from nowplaying.util.time import UTC_TZ


def get_client() -> AsyncClient:
    return AsyncClient(
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en;q=0.8',
            'DNT': '1',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        },
        follow_redirects=True,
        # last.fm doesn't like ipv6 idk why. when requesting with ipv6 it returns 403
        transport=AsyncHTTPTransport(local_address='0.0.0.0'),
        proxy=config.LASTFM_SEARCH_PROXY,
        verify=not config.LASTFM_SEARCH_PROXY,
        timeout=Timeout(5.0, read=None),
    )


PLAY_LINKS_REGEX = re_compile(r'<ul\sclass="play-this-track-playlinks">(.*?)</ul>', DOTALL)
HREF_URL_REGEX = re_compile('href="(https://.{1,100})"')
PAGE_RESOURCE_NAME_REGEX = re_compile('data-page-resource-name="(.{1,256})"')
PAGE_RESOURCE_ARTIST_NAME_REGEX = re_compile('data-page-resource-artist-name="(.{1,256})"')


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


@dataclass
class LastFMTrackFromURL:
    track: LastFMTrack
    external_urls: list[str]


def _reorder_external_links(links: list[str]) -> list[str]:
    def _sort_key(link: str) -> int:
        # 1. Spotify
        if 'spotify.com' in link:
            return 0
        # 2. Apple Music
        if 'apple.com' in link:
            return 1
        # 4. YouTube with the lowest priority
        if 'youtube.com' in link:
            return 4
        # 3. Everything else
        return 3

    return sorted(links, key=_sort_key)


@alru_cache()
async def query_last_fm_url(track_url: str) -> LastFMTrackFromURL:
    response: Response | None = None

    # Retry 5 times
    for _ in range(5):
        async with get_client() as client:
            try:
                response = await client.get(track_url)
            except HTTPError:
                # Retry on errors
                continue
            break

    if not response:
        msg = '(last.fm) All queries got timed out'
        raise ValueError(msg)

    if response.status_code != STATUS_OK:
        msg = f'(last.fm) Got status code {response.status_code}: {response.text}'
        raise ValueError(msg)

    name_match = search(PAGE_RESOURCE_NAME_REGEX, response.text)
    artist_match = search(PAGE_RESOURCE_ARTIST_NAME_REGEX, response.text)

    track = LastFMTrackFromURL(
        track=LastFMTrack(
            url=track_url,
            artist=unescape(artist_match.group(1)) if artist_match else '',
            name=unescape(name_match.group(1)) if name_match else '',
        ),
        external_urls=[],
    )

    container = search(PLAY_LINKS_REGEX, response.text)
    if container is None:
        return track

    external_urls = set(findall(HREF_URL_REGEX, container.group(1)))
    track.external_urls = _reorder_external_links(list(map(unescape, external_urls)))
    return track


def _unavailable() -> NoReturn:
    raise PlatformTemporarilyUnavailableError(platform=SongLinkPlatformType.LASTFM)


def _ensure_response(response: Response) -> None:
    if is_serverside_error(response.status_code):
        _unavailable()
    if response.status_code != STATUS_OK:
        msg = f'status {response.status_code} != 200 {response.text}'
        raise LastFMError(msg)


class LastFMClient:
    def __init__(self, session_key: str | None = None, token: str | None = None) -> None:
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

    async def get_session_key(self) -> str:
        if self.token is None:
            raise LastFMError

        try:
            response = await self.client.get(
                self.base_url,
                params=self._build_query(
                    'auth.getSession',
                    token=self.token,
                ),
            )
        except HTTPError:
            _unavailable()
        _ensure_response(response)

        session_data = orjson.loads(response.content)
        session_key: str | None = session_data.get('session', {}).get('key', None)
        if session_key is None:
            raise LastFMError

        return session_key

    async def get_username(self) -> str:
        if self.session_key is None:
            raise LastFMError

        try:
            response = await self.client.get(self.base_url, params=self._build_query('user.getInfo'))
        except HTTPError:
            _unavailable()

        _ensure_response(response)
        user_data = orjson.loads(response.content)
        return user_data['user']['name']

    async def get_recent_tracks(self, limit: int) -> list[LastFMPlayedTrack]:
        if self.session_key is None:
            raise LastFMError

        try:
            response = await self.client.get(
                self.base_url,
                params=self._build_query(
                    'user.getRecentTracks',
                    user=await self.get_username(),
                    limit=str(limit),
                ),
            )
        except HTTPError:
            _unavailable()

        _ensure_response(response)
        response_data = orjson.loads(response.content)

        played_tracks: list[LastFMPlayedTrack] = []
        for track in response_data.get('recenttracks', {}).get('track', []):
            is_now_playing: bool = track.get('@attr', {}).get('nowplaying', False)

            played_ts: str | None = track.get('date', {}).get('uts', None)
            played_at = (
                datetime.now(tz=UTC_TZ) if played_ts is None else datetime.fromtimestamp(int(played_ts), tz=UTC_TZ)
            )

            played_tracks.append(
                LastFMPlayedTrack(
                    is_now_playing=is_now_playing,
                    track=LastFMTrack(
                        url=track['url'],
                        artist=track['artist']['#text'],
                        name=track['name'],
                    ),
                    playback_date=played_at,
                )
            )

        return played_tracks

    def _get_signature(self, query_params: dict[str, str]) -> str:
        string = ''
        for name in sorted(query_params.keys()):
            string += f'{name}{query_params[name]}'

        string += self.api_secret

        hashed = md5(usedforsecurity=False)
        hashed.update(string.encode('utf-8'))
        return hashed.hexdigest()

    def _build_query(self, method: str, **kwargs: str) -> dict[str, str]:
        kwargs['method'] = method
        kwargs['api_key'] = self.api_key
        if self.session_key is not None:
            kwargs['sk'] = self.session_key
        kwargs['api_sig'] = self._get_signature(kwargs)
        kwargs['format'] = 'json'
        return kwargs
