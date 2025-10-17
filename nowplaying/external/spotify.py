from abc import ABC, abstractmethod
from base64 import b64encode
from time import time
from typing import NoReturn, cast

import orjson
from httpx import AsyncClient, HTTPError, Response

from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTemporarilyUnavailableError
from nowplaying.util.http import (
    STATUS_BAD_REQUEST,
    STATUS_FORBIDDEN,
    STATUS_NO_CONTENT,
    STATUS_NOT_FOUND,
    STATUS_OK,
    is_serverside_error,
)


class SpotifyError(Exception):
    """Spotify error base."""


class SpotifyNoTokenError(SpotifyError):
    """Would be raised if you try to access an endpoint that requires a token without token."""


class SpotifyInvalidStatusCodeError(SpotifyError):
    """Would be raised if you try to access an endpoint that requires a token without token."""


class SpotifyPremiumRequiredError(SpotifyError):
    """Would be raised if you try to access an endpoint that requires a premium license."""


class SpotifyInvalidTokenScopeError(SpotifyError):
    """Would be raised if the token scope is invalid."""


class SpotifyCacheHandlerABC(ABC):
    @abstractmethod
    async def get_cached_token(self) -> dict[str, str | int] | None:
        """Get the token dict."""

    @abstractmethod
    async def save_token_to_cache(self, token_info: dict[str, str | int]) -> None:
        """Save the token dict."""


SpotifyToken = dict[str, int | str]


def _is_scope_subset(needle_scope: str, haystack_scope: str) -> bool:
    needle_scope_set = set(needle_scope.split(','))
    haystack_scope_set = set(haystack_scope.split(','))
    return needle_scope_set <= haystack_scope_set


def _is_token_expired(token_info: SpotifyToken) -> bool:
    now = int(time())
    expires_at: int = int(token_info['expires_at'])
    return expires_at - now < 60  # noqa: PLR2004


def _unavailable() -> NoReturn:
    raise PlatformTemporarilyUnavailableError(platform=SongLinkPlatformType.SPOTIFY)


def _raise_for_status(response: Response) -> None:
    if is_serverside_error(response.status_code):
        _unavailable()

    if response.status_code == STATUS_FORBIDDEN and 'PREMIUM_REQUIRED' in response.text:
        msg = f'{response.status_code}: {response.text}'
        raise SpotifyPremiumRequiredError(msg)

    if response.status_code not in {STATUS_OK, STATUS_NO_CONTENT}:
        msg = f'{response.status_code}: {response.text}'
        raise SpotifyInvalidStatusCodeError(msg)


def _is_clientside_error(response: Response) -> bool:
    return response.status_code in {STATUS_BAD_REQUEST, STATUS_NOT_FOUND}


class Spotify:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str,
        cache_handler: SpotifyCacheHandlerABC,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._scope = scope
        self._cache_handler = cache_handler

        self._token: SpotifyToken | None = None

        self._client = AsyncClient(
            headers={
                'User-Agent': 'playinnowbot',
            }
        )

        self._basic_auth_header: str | None = None

        self._api_base = 'https://api.spotify.com/v1/'.rstrip('/')
        self._oauth_token_url = 'https://accounts.spotify.com/api/token'  # noqa: S105

    async def gather_token(self) -> None:
        self._token = await self._validate_token(
            await self._cache_handler.get_cached_token(),
        )

    async def get_access_token(self, auth_code: str) -> dict:
        try:
            response = await self._client.post(
                self._oauth_token_url,
                data={
                    'redirect_uri': self._redirect_uri,
                    'code': auth_code,
                    'grant_type': 'authorization_code',
                    'scope': self._scope,
                },
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        _raise_for_status(response)

        token = orjson.loads(response.content)
        token = self._add_attrs_to_token(token)
        await self._cache_handler.save_token_to_cache(token)
        return token

    async def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            response = await self._client.post(
                self._oauth_token_url,
                data={
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token',
                },
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        _raise_for_status(response)

        token = orjson.loads(response.content)
        token = self._add_attrs_to_token(token)
        if 'refresh_token' not in token:
            token['refresh_token'] = refresh_token
        await self._cache_handler.save_token_to_cache(token)
        return token

    async def get_current_user_playing_track(self) -> dict | None:
        if self._token is None:
            raise SpotifyNoTokenError

        try:
            response = await self._client.get(
                f'{self._api_base}/me/player/currently-playing',
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        _raise_for_status(response)

        if response.status_code == STATUS_NO_CONTENT:
            return None

        return orjson.loads(response.content)

    async def get_current_user_recently_played(self, limit: int = 50) -> dict:
        if self._token is None:
            raise SpotifyNoTokenError

        try:
            response = await self._client.get(
                f'{self._api_base}/me/player/recently-played',
                headers=self._auth_headers,
                params={'limit': str(limit)},
            )
        except HTTPError:
            _unavailable()
        _raise_for_status(response)

        return orjson.loads(response.content)

    async def get_track(self, track_id: str) -> dict | None:
        if self._token is None:
            raise SpotifyNoTokenError

        try:
            response = await self._client.get(
                f'{self._api_base}/tracks/{track_id}',
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        if _is_clientside_error(response):
            return None

        _raise_for_status(response)
        return orjson.loads(response.content)

    async def add_to_queue(self, track_uri: str) -> bool:
        if self._token is None:
            raise SpotifyNoTokenError

        try:
            response = await self._client.post(
                f'{self._api_base}/me/player/queue',
                params={'uri': track_uri},
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        if _is_clientside_error(response):
            return False

        _raise_for_status(response)
        return True

    async def start_playback(self, uri: str) -> None:
        # Enqueue and skip to it.
        # If we use the /me/player/play endpoint,
        #   it will clear the queue and start playing the track
        if not await self.add_to_queue(uri):
            return

        try:
            response = await self._client.post(
                f'{self._api_base}/me/player/next',
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()
        if _is_clientside_error(response):
            return

        _raise_for_status(response)

    async def like(self, track_uri: str) -> None:
        if self._token is None:
            raise SpotifyNoTokenError

        # if scopes don't match, then bail
        if not _is_scope_subset('user-library-modify', cast(str, self._token.get('scope', ''))):
            raise SpotifyInvalidTokenScopeError

        try:
            response = await self._client.put(
                f'{self._api_base}/me/tracks',
                json={'ids': [track_uri]},
                headers=self._auth_headers,
            )
        except HTTPError:
            _unavailable()

        _raise_for_status(response)

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self._token is not None:
            return {'Authorization': f'Bearer {self._token["access_token"]}'}

        if self._basic_auth_header is None:
            auth_header_str = f'{self._client_id}:{self._client_secret}'
            auth_header_b64 = b64encode(auth_header_str.encode('ascii'))
            auth_header = auth_header_b64.decode('ascii')
            self._basic_auth_header = f'Basic {auth_header}'

        return {'Authorization': self._basic_auth_header}

    def _add_attrs_to_token(self, token: SpotifyToken) -> SpotifyToken:
        token['expires_at'] = int(time()) + cast(int, token['expires_in'])
        token['scope'] = self._scope
        return token

    async def _validate_token(
        self,
        token_info: SpotifyToken | None,
    ) -> SpotifyToken | None:
        if token_info is None:
            return None

        if _is_token_expired(token_info):
            token_info = await self.refresh_access_token(
                cast(str, token_info['refresh_token']),
            )

        return token_info
