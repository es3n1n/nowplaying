from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt
import orjson
from async_lru import alru_cache
from httpx import AsyncClient, Response

from ..core.config import config
from ..util.http import STATUS_NOT_FOUND, STATUS_OK
from ..util.logger import logger


SESSION_LIVE_TIME: timedelta = timedelta(hours=6)

client = AsyncClient(headers={
    'Pragma': 'no-cache',
    'Origin': 'https://odesli.co',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 '
        + 'Safari/537.36'
    ),
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Cache-Control': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Referer': 'https://odesli.co/',
    'DNT': '1',
})


@alru_cache()
async def find_song_in_apple_music(artist: str, name: str, country: str = 'US') -> int | None:
    resp = await client.get('https://itunes.apple.com/search', params={
        'term': f'{artist} - {name}',
        'country': country,
        'entity': 'song',
    })

    try:
        resp_json = orjson.loads(resp.text)
    except orjson.JSONDecodeError:
        return None

    if 'results' not in resp_json:
        logger.warning(f'Got suspicious response from itunes: {resp_json}')
        return None

    search_results = resp_json['results']
    if not search_results:
        return None

    return search_results[0]['trackId']


class AppleMusicError(Exception):
    """Apple music base error class."""


class AppleMusicInvalidResultCodeError(AppleMusicError):
    """Would be raise if response code isn't 200."""


@dataclass
class AppleMusicTrack:
    id: str
    url: str
    artist: str
    name: str

    @classmethod
    def load(cls, track: dict) -> 'AppleMusicTrack':
        return cls(
            id=track['id'],
            url=track['attributes']['url'],
            artist=track['attributes']['artistName'],
            name=track['attributes']['name'],
        )


def _validate_response_code(response: Response) -> None:
    if response.status_code != STATUS_OK:
        raise AppleMusicInvalidResultCodeError(str(response.status_code))


class AppleMusicWrapperClient:
    def __init__(self, app: 'AppleMusicWrapper', media_user_token: str):
        self.app = app
        self.media_user_token = media_user_token

    def headers(self, with_media_token: bool = False) -> dict[str, str]:
        headers_result = self.app.headers
        if with_media_token:
            headers_result['media-user-token'] = self.media_user_token
        return headers_result

    # limit includes the currently playing track
    async def recently_played(self, limit: int) -> list[AppleMusicTrack]:
        response = await self.app.client.get(
            'https://api.music.apple.com/v1/me/recent/played/tracks',
            headers=self.headers(with_media_token=True),
            params={
                'limit': str(limit),
            },
        )
        _validate_response_code(response)

        response_json = orjson.loads(response.content)
        if 'data' not in response_json:
            raise AppleMusicError('got a weird json')

        out_tracks = []
        for track in response_json['data']:
            # Skip custom uploaded tracks
            if 'id' not in track:
                continue

            out_tracks.append(AppleMusicTrack.load(track))

        return out_tracks

    async def get_track(self, track_id: str) -> AppleMusicTrack | None:
        # fixme: instead of using US we should store the appropriate store id
        response = await self.app.client.get(
            f'https://api.music.apple.com/v1/catalog/us/songs/{track_id}',
            headers=self.headers(),
        )

        if response.status_code == STATUS_NOT_FOUND:
            return None

        _validate_response_code(response)
        response_json = orjson.loads(response.content)

        if not response_json['data']:
            raise AppleMusicError('got a weird track response huh?')

        return AppleMusicTrack.load(response_json['data'][0])


class AppleMusicWrapper:
    def __init__(self) -> None:
        self.secret = config.APPLE_SECRET_KEY
        self.key_id = config.APPLE_KEY_ID
        self.team_id = config.APPLE_TEAM_ID
        self.client = AsyncClient(headers={
            'User-Agent': 'playinnow/1.0',
            'Origin': config.WEB_SERVER_PUBLIC_ENDPOINT,
        })

        self._origins: list[str] = [config.WEB_SERVER_PUBLIC_ENDPOINT]

        self._alg: str = 'ES256'

        self._token: str | None = None
        self._token_exp: datetime = datetime.utcnow()

    def with_media_token(self, media_token: str) -> 'AppleMusicWrapperClient':
        return AppleMusicWrapperClient(self, media_token)

    @property
    def ensured_token(self) -> str:
        if self.token_valid:
            if not self._token:
                raise ValueError('No token')
            return self._token

        now = datetime.utcnow()
        self._token_exp = now + SESSION_LIVE_TIME
        self._token = jwt.encode(
            payload={
                'iss': self.team_id,
                'iat': int(now.timestamp()),
                'exp': int(self._token_exp.timestamp()),
                'origin': self._origins,
            },
            headers={
                'alg': self._alg,
                'kid': self.key_id,
            },
            key=self.secret,
            algorithm=self._alg,
        )
        return self._token

    @property
    def headers(self) -> dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.ensured_token}',
        }

    @property
    def token_valid(self) -> bool:
        if self._token is None:
            return False

        dt = datetime.utcnow()
        return dt <= self._token_exp
