from dataclasses import dataclass
from typing import Any, NoReturn

import orjson
from httpx import AsyncClient, HTTPError, Response

from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTemporarilyUnavailableError
from nowplaying.util.http import STATUS_NOT_FOUND, STATUS_OK, is_serverside_error
from nowplaying.util.user_agents import get_random_user_agent


class SoundCloudError(Exception):
    """SoundCloud base error class."""


class SoundCloudInvalidResponseCodeError(SoundCloudError):
    """Would be raise if response code isn't 200."""


class SoundCloudMalformedResponseError(SoundCloudError):
    """Would be raise if response is malformed."""


@dataclass(frozen=True)
class SoundCloudTrack:
    id: int
    permalink_url: str
    title: str
    author: str

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> 'SoundCloudTrack':
        author = data['user']['username']

        publisher_metadata = data.get('publisher_metadata')
        if publisher_metadata:
            author = publisher_metadata.get('artist') or author

        return cls(
            id=data['id'],
            permalink_url=data['permalink_url'],
            title=data['title'],
            author=author,
        )


@dataclass(frozen=True)
class SoundCloudHistoryTrack:
    played_at: int
    track: SoundCloudTrack


def _unavailable() -> NoReturn:
    raise PlatformTemporarilyUnavailableError(platform=SongLinkPlatformType.SOUNDCLOUD)


def _validate_response_code(response: Response) -> None:
    if is_serverside_error(response.status_code):
        _unavailable()
    if response.status_code != STATUS_OK:
        raise SoundCloudInvalidResponseCodeError(str(response.status_code))


class SoundCloudWrapper:
    def __init__(self, oauth_token: str) -> None:
        self._client = AsyncClient(
            headers={
                'User-Agent': get_random_user_agent(chrome=True),
                'Authorization': f'OAuth {oauth_token}',
                'Origin': 'https://soundcloud.com',
                'Referer': 'https://soundcloud.com/',
            },
            params={
                'client_id': 'xXKzFLdhfXAtbaLbKFp4cNoiduLizuYO',
                'app_version': '1765442274',
                'app_locale': 'en',
            },
        )
        self._api_base = 'https://api-v2.soundcloud.com/'

    async def get_play_history(self, limit: int = 25, offset: int = 0) -> list[SoundCloudHistoryTrack]:
        try:
            resp = await self._client.get(
                f'{self._api_base}me/play-history/tracks',
                params={
                    'limit': str(limit),
                    'offset': str(offset),
                    'linked_partitioning': '1',
                },
            )
        except HTTPError:
            _unavailable()
        _validate_response_code(resp)

        try:
            data = orjson.loads(resp.content)
        except orjson.JSONDecodeError as err:
            raise SoundCloudMalformedResponseError from err

        return [
            SoundCloudHistoryTrack(
                played_at=item['played_at'] // 1000,  # convert ms to seconds
                track=SoundCloudTrack.deserialize(item['track']),
            )
            for item in data['collection']
        ]

    async def get_track(self, track_id: int) -> SoundCloudTrack | None:
        try:
            resp = await self._client.get(f'{self._api_base}tracks/{track_id}')
        except HTTPError:
            _unavailable()

        if resp.status_code == STATUS_NOT_FOUND:
            return None
        _validate_response_code(resp)

        try:
            data = orjson.loads(resp.content)
        except orjson.JSONDecodeError as err:
            raise SoundCloudMalformedResponseError from err

        return SoundCloudTrack.deserialize(data)
