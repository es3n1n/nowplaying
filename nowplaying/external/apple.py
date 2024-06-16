from datetime import datetime, timedelta

import jwt
from async_lru import alru_cache
from httpx import AsyncClient
from orjson import JSONDecodeError, loads

from ..core.config import config
from ..util.logger import logger


SESSION_LIVE_TIME: timedelta = timedelta(hours=24)

client = AsyncClient(headers={
    'Pragma': 'no-cache',
    'Origin': 'https://odesli.co',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 '
                  'Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Cache-Control': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Referer': 'https://odesli.co/',
    'DNT': '1',
})


@alru_cache(maxsize=128)
async def find_song_in_apple_music(artist: str, name: str, country: str = 'US') -> int | None:
    resp = await client.get('https://itunes.apple.com/search', params={
        'term': f'{artist} - {name}',
        'country': country,
        'entity': 'song',
    })

    try:
        resp_json = loads(resp.text)
    except JSONDecodeError:
        return None

    if 'results' not in resp_json:
        logger.warning(f'Got suspicious response from itunes: {resp_json}')
        return None

    results = resp_json['results']
    if len(results) == 0:
        return None

    return results[0]['trackId']


class AppleMusicWrapperClient:
    def __init__(self, app: 'AppleMusicWrapper', media_user_token: str):
        self.app = app
        self.media_user_token = media_user_token

    def headers(self, with_media_token: bool = False) -> dict[str, str]:
        result = self.app.headers
        if with_media_token:
            result['media-user-token'] = self.media_user_token
        return result


class AppleMusicWrapper:
    def __init__(self) -> None:
        self.secret = config.APPLE_SECRET_KEY
        self.key_id = config.APPLE_KEY_ID
        self.team_id = config.APPLE_TEAM_ID
        self.client = AsyncClient(headers={
            'User-Agent': 'playinnow/1.0'
        })

        self._alg: str = 'ES256'

        self._token: str | None = None
        self._token_exp: datetime = datetime.utcnow()

    def with_media_token(self, media_token: str) -> 'AppleMusicWrapperClient':
        return AppleMusicWrapperClient(self, media_token)

    @property
    def ensured_token(self) -> str:
        if self.token_valid:
            assert self._token is not None
            return self._token

        now = datetime.utcnow()
        self._token_exp = now + SESSION_LIVE_TIME
        self._token = jwt.encode(
            payload={
                'iss': self.team_id,
                'iat': int(now.timestamp()),
                'exp': int(self._token_exp.timestamp()),
            },
            headers={
                'alg': self._alg,
                'kid': self.key_id,
            },
            key=self.secret,
            algorithm=self._alg
        )
        return self._token

    @property
    def headers(self) -> dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.ensured_token}'
        }

    @property
    def token_valid(self) -> bool:
        if self._token is None:
            return False

        dt = datetime.utcnow()
        return dt <= self._token_exp
