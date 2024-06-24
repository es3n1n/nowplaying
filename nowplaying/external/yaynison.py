# Ported from https://github.com/bulatorr/go-yaynison/
from dataclasses import dataclass
from typing import List

import orjson
from websockets import WebSocketClientProtocol, connect, headers
from websockets.exceptions import WebSocketException


def do_nothing(*args, **kwargs) -> None:  # noqa: WPS324
    return None  # noqa: WPS324


# Workaround for ticket's json subprotocol
headers.validate_subprotocols.__code__ = do_nothing.__code__


class YaynisonError(Exception):
    """Ynison exception."""


@dataclass
class YanisonPlayableItem:
    playable_id: str
    album_id: str | None
    from_item: str
    title: str  # might be empty, not sure why


class Yaynison:
    def __init__(self, token: str):
        self._token = token
        self._device = 'playinnowbot'
        self._headers = [
            ('Origin', 'https://music.yandex.ru'),
            ('Authorization', f'OAuth {self._token}'),
        ]

        self._connection_uri: str | None = None
        self._redirect_ticket: str | None = None
        self._session_id: str | None = None

        self._config_message: str = orjson.dumps({
            'update_full_state': {
                'player_state': {
                    'player_queue': {
                        'current_playable_index': -1,
                        'entity_id': '',
                        'entity_type': 'VARIOUS',
                        'playable_list': [],
                        'options': {'repeat_mode': 'NONE'},
                        'entity_context': 'BASED_ON_ENTITY_BY_DEFAULT',
                        'version': {
                            'device_id': self._device,
                            'version': 9021243204784341000,
                            'timestamp_ms': 0,
                        },
                        'from_optional': '',
                    },
                    'status': {
                        'duration_ms': 0,
                        'paused': True,
                        'playback_speed': 1,
                        'progress_ms': 0,
                        'version': {
                            'device_id': self._device,
                            'version': 8321822175199937000,
                            'timestamp_ms': 0,
                        },
                    },
                },
                'device': {
                    'capabilities': {
                        'can_be_player': False,
                        'can_be_remote_controller': False,
                        'volume_granularity': 0,
                    },
                    'info': {
                        'device_id': self._device,
                        'type': 'WEB',
                        'title': 'playinnowbot',
                        'app_name': 'Chrome',
                    },
                    'volume_info': {'volume': 0},
                    'is_shadow': True,
                },
                'is_currently_active': False,
            },
            'rid': 'ac281c26-a047-4419-ad00-e4fbfda1cba3',
            'player_action_timestamp_ms': 0,
            'activity_interception_type': 'DO_NOT_INTERCEPT_BY_DEFAULT',
        }).decode()

        self._conn: WebSocketClientProtocol | None = None

    async def startup(self):
        await self.request_ticket()
        await self.connect()

    async def request_ticket(self) -> None:
        try:
            conn = await connect(
                'wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison',
                extra_headers=self._headers,
                subprotocols=self._subprotocols,  # type: ignore
                compression=None,
            )
        except WebSocketException:
            raise YaynisonError('unable to connect to ynison redirect')

        try:
            message = orjson.loads(await conn.recv())
        except WebSocketException:
            raise YaynisonError('unable to get the ticket')

        await conn.close()
        if 'error' in message:
            raise YaynisonError('got an error in ticket logic')

        self._connection_uri = f'wss://{message["host"]}/ynison_state.YnisonStateService/PutYnisonState'
        self._redirect_ticket = message['redirect_ticket']
        self._session_id = message['session_id']

    async def disconnect(self) -> None:
        if self._conn is None:
            return

        await self._conn.close()

    async def connect(self) -> None:
        if self._connection_uri is None:
            await self.request_ticket()

            if self._connection_uri is None:
                raise ValueError('no ticket')

        try:
            self._conn = await connect(
                self._connection_uri,
                extra_headers=self._headers,
                subprotocols=self._subprotocols,  # type: ignore
                compression=None,
            )
        except WebSocketException:
            raise YaynisonError('unable to connect to yaynison')

        try:
            await self._conn.send(self._config_message)
        except WebSocketException:
            await self.disconnect()
            raise YaynisonError('unable to send message to yaynison')

    async def get_playable_items(self) -> List[YanisonPlayableItem]:
        if self._conn is None:
            await self.connect()

            if self._conn is None:
                raise ValueError('conn is none')

        playable = []

        message = orjson.loads(await self._conn.recv())
        player_queue = message.get('player_state', {}).get('player_queue', {})
        current_index = player_queue.get('current_playable_index', 0)

        # todo: iterate in reverse order
        for it in player_queue.get('playable_list', [])[current_index:]:
            if it['playable_type'] != 'TRACK':
                continue

            playable.append(YanisonPlayableItem(
                playable_id=it['playable_id'],
                album_id=it.get('album_id_optional', None),
                from_item=it['from'],
                title=it['title'],
            ))

        return playable

    async def one_shot_playable_items(self) -> List[YanisonPlayableItem]:
        await self.startup()
        playable_items = await self.get_playable_items()
        await self.disconnect()
        return playable_items

    @property
    def _ticket_subprotocol(self) -> str:
        subprotocol_data = {
            'Ynison-Device-Id': self._device,
            'Ynison-Device-Info': '{"app_name":"Chrome","type":1}',
        }

        if self._redirect_ticket is not None:
            subprotocol_data['Ynison-Redirect-Ticket'] = self._redirect_ticket

        if self._session_id is not None:
            subprotocol_data['Ynison-Session-Id'] = self._session_id

        return orjson.dumps(subprotocol_data).decode()

    @property
    def _subprotocols(self) -> List[str]:
        return ['Bearer', 'v2', self._ticket_subprotocol]
