from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt
import orjson
from httpx import AsyncClient, Response

from nowplaying.core.config import config
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTemporarilyUnavailableError
from nowplaying.util.http import STATUS_NOT_FOUND, STATUS_OK, is_serverside_error
from nowplaying.util.time import UTC_TZ


SESSION_LIVE_TIME: timedelta = timedelta(hours=6)


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
    is_local: bool

    @classmethod
    def load(cls, track: dict) -> 'AppleMusicTrack':
        return cls(
            id=track['id'],
            url=track['attributes']['url'],
            artist=track['attributes']['artistName'],
            name=track['attributes']['name'],
            is_local='url' not in track['attributes'],
        )


def _validate_response_code(response: Response) -> None:
    if is_serverside_error(response.status_code):
        raise PlatformTemporarilyUnavailableError(platform=SongLinkPlatformType.APPLE)
    if response.status_code != STATUS_OK:
        raise AppleMusicInvalidResultCodeError(str(response.status_code))


class AppleMusicWrapperClient:
    def __init__(self, app: 'AppleMusicWrapper', media_user_token: str) -> None:
        self.app = app
        self.media_user_token = media_user_token

    def headers(self, *, with_media_token: bool = False) -> dict[str, str]:
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
            msg = 'got a weird json'
            raise AppleMusicError(msg)

        return [AppleMusicTrack.load(track) for track in response_json['data']]

    async def get_track(self, track_id: str) -> AppleMusicTrack | None:
        # TODO(es3n1n): instead of using US we should store the appropriate store id
        response = await self.app.client.get(
            f'https://api.music.apple.com/v1/catalog/us/songs/{track_id}',
            headers=self.headers(),
        )

        if response.status_code == STATUS_NOT_FOUND:
            return None

        _validate_response_code(response)
        response_json = orjson.loads(response.content)

        if not response_json['data']:
            msg = 'got a weird track response huh?'
            raise AppleMusicError(msg)

        return AppleMusicTrack.load(response_json['data'][0])


class AppleMusicWrapper:
    def __init__(self) -> None:
        self.secret = config.APPLE_SECRET_KEY
        self.key_id = config.APPLE_KEY_ID
        self.team_id = config.APPLE_TEAM_ID
        self.client = AsyncClient(
            headers={
                'User-Agent': 'playinnow/1.0',
                'Origin': config.WEB_SERVER_PUBLIC_ENDPOINT,
            }
        )

        self._origins: list[str] = [config.WEB_SERVER_PUBLIC_ENDPOINT]

        self._alg: str = 'ES256'

        self._token: str | None = None
        self._token_exp: datetime = datetime.now(tz=UTC_TZ)

    def with_media_token(self, media_token: str) -> 'AppleMusicWrapperClient':
        return AppleMusicWrapperClient(self, media_token)

    @property
    def ensured_token(self) -> str:
        if self.token_valid:
            if not self._token:
                msg = 'No token'
                raise ValueError(msg)
            return self._token

        now = datetime.now(tz=UTC_TZ)
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

        dt = datetime.now(tz=UTC_TZ)
        return dt <= self._token_exp
