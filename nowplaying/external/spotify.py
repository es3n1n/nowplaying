from abc import ABC, abstractmethod
from base64 import b64encode
from time import time

from httpx import AsyncClient, Response
from orjson import loads


class SpotifyError(Exception):
    pass


class SpotifyCacheHandlerABC(ABC):
    @abstractmethod
    async def get_cached_token(self) -> dict[str, str | int] | None:
        """ get the token dict """

    @abstractmethod
    async def save_token_to_cache(self, token_info: dict[str, str | int]) -> None:
        """ save the token dict"""


SpotifyToken = dict[str, int | str]


class Spotify:
    def __init__(
            self,
            client_id: str,
            client_secret: str,
            redirect_uri: str,
            scope: str,
            cache_handler: SpotifyCacheHandlerABC
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.cache_handler = cache_handler

        self.token: SpotifyToken | None = None

        self.client = AsyncClient(headers={
            'User-Agent': 'playinnowbot'
        })

        self.basic_auth_header: str | None = None

        self.api_base = 'https://api.spotify.com/v1/'.rstrip('/')
        self.oauth_token_url = 'https://accounts.spotify.com/api/token'

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self.token is not None:
            return {
                'Authorization': f'Bearer {self.token["access_token"]}'
            }

        if self.basic_auth_header is None:
            auth_header_b64 = b64encode(f'{self.client_id}:{self.client_secret}'.encode('ascii'))
            self.basic_auth_header = f'Basic {auth_header_b64.decode("ascii")}'

        return {
            'Authorization': self.basic_auth_header
        }

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        if response.status_code not in [200, 204]:
            raise SpotifyError(f'status {response.status_code} != 200 {response.text}')

    @staticmethod
    def _is_clientside_error(response: Response) -> bool:
        return response.status_code in [400, 404]

    def _add_attrs_to_token(self, token: SpotifyToken) -> SpotifyToken:
        token['expires_at'] = int(time()) + token['expires_in']  # type: ignore
        token['scope'] = self.scope
        return token

    @staticmethod
    def _is_scope_subset(needle_scope: str, haystack_scope: str) -> bool:
        needle_scope_set = set(needle_scope.split()) if needle_scope else set()
        haystack_scope_set = (
            set(haystack_scope.split()) if haystack_scope else set()
        )
        return needle_scope_set <= haystack_scope_set

    @staticmethod
    def _is_token_expired(token_info: SpotifyToken) -> bool:
        now = int(time())
        expires_at: int = token_info['expires_at']  # type: ignore
        return expires_at - now < 60

    async def _validate_token(
            self,
            token_info: SpotifyToken | None
    ) -> SpotifyToken | None:
        if token_info is None:
            return None

        # if scopes don't match, then bail
        if 'scope' not in token_info or not self._is_scope_subset(
                self.scope, token_info['scope']  # type: ignore
        ):
            return None

        if self._is_token_expired(token_info):
            token_info = await self.refresh_access_token(
                token_info['refresh_token']  # type: ignore
            )

        return token_info

    async def gather_token(self) -> None:
        self.token = await self._validate_token(
            await self.cache_handler.get_cached_token()
        )

    async def get_access_token(self, auth_code: str) -> None:
        response = await self.client.post(
            self.oauth_token_url,
            data={
                'redirect_uri': self.redirect_uri,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'scope': self.scope
            },
            headers=self._auth_headers
        )
        self._raise_for_status(response)

        token = loads(response.content)
        token = self._add_attrs_to_token(token)
        await self.cache_handler.save_token_to_cache(token)

    async def refresh_access_token(self, refresh_token: str) -> dict:
        # todo test
        response = await self.client.post(
            self.oauth_token_url,
            data={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            },
            headers=self._auth_headers
        )
        self._raise_for_status(response)

        token = loads(response.content)
        token = self._add_attrs_to_token(token)
        if 'refresh_token' not in token:
            token['refresh_token'] = refresh_token
        await self.cache_handler.save_token_to_cache(token)
        return token

    async def get_current_user_playing_track(self) -> dict | None:
        if self.token is None:
            raise SpotifyError('token is none')

        response = await self.client.get(
            f'{self.api_base}/me/player/currently-playing',
            headers=self._auth_headers
        )
        self._raise_for_status(response)

        if response.status_code == 204:  # No content
            return None

        return loads(response.content)

    async def get_current_user_recently_played(self, limit: int = 50) -> dict:
        if self.token is None:
            raise SpotifyError('token is none')

        response = await self.client.get(
            f'{self.api_base}/me/player/recently-played',
            headers=self._auth_headers,
            params={'limit': str(limit)}
        )
        self._raise_for_status(response)

        return loads(response.content)

    async def get_track(self, track_id: str) -> dict | None:
        if self.token is None:
            raise SpotifyError('token is none')

        response = await self.client.get(
            f'{self.api_base}/tracks/{track_id}',
            headers=self._auth_headers
        )
        if self._is_clientside_error(response):
            return None

        self._raise_for_status(response)
        return loads(response.content)

    async def add_to_queue(self, track_uri: str) -> None:
        if self.token is None:
            raise SpotifyError('token is none')

        response = await self.client.post(
            f'{self.api_base}/me/player/queue',
            params={'uri': track_uri},
            headers=self._auth_headers
        )
        if self._is_clientside_error(response):
            return None

        self._raise_for_status(response)

    async def start_playback(self, uris: list[str]) -> None:
        if self.token is None:
            raise SpotifyError('token is none')

        response = await self.client.put(
            f'{self.api_base}/me/player/play',
            json={'uris': uris},
            headers=self._auth_headers
        )
        if self._is_clientside_error(response):
            return None

        self._raise_for_status(response)
