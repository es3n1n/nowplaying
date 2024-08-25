# Ported from https://github.com/bulatorr/go-yaynison/
from dataclasses import dataclass
from uuid import uuid4

import orjson
from aiohttp import ClientError, ClientSession, ClientWebSocketResponse


class YaynisonError(Exception):
    """Ynison exception."""


@dataclass
class YanisonPlayableItem:
    playable_id: str
    album_id: str | None
    from_item: str
    title: str  # might be empty, not sure why


class Yaynison:
    def __init__(self, token: str) -> None:
        self._token = token
        self._device = 'playinnowbot'
        self._queue_version = 9021243204784341000
        self._status_version = 8321822175199937000

        self._connection_uri: str | None = None
        self._redirect_ticket: str | None = None
        self._session_id: str | None = None

        self._config_message: str = orjson.dumps(
            {
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
                                'version': self._queue_version,
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
                                'version': self._status_version,
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
                            'title': self._device,
                            'app_name': 'Chrome',
                        },
                        'volume_info': {'volume': 0},
                        'is_shadow': True,
                    },
                    'is_currently_active': False,
                },
                'rid': str(uuid4()),
                'player_action_timestamp_ms': 0,
                'activity_interception_type': 'DO_NOT_INTERCEPT_BY_DEFAULT',
            }
        ).decode()

    async def one_shot_playable_items(self) -> list[YanisonPlayableItem]:
        await self.request_ticket()
        return await self.get_playable_items()

    async def request_ticket(self) -> None:
        async with (
            ClientSession() as session,
            session.ws_connect(
                'wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison',
                headers=self._headers,
            ) as ws,
        ):
            try:
                await self._obtain_ticket(ws)
            except ClientError as err:
                msg = 'unable to obtain ticket'
                raise YaynisonError(msg) from err

    async def get_playable_items(self) -> list[YanisonPlayableItem]:
        if self._connection_uri is None:
            msg = 'no ticket'
            raise ValueError(msg)

        async with (
            ClientSession() as session,
            session.ws_connect(
                self._connection_uri,
                headers=self._headers,
            ) as ws,
        ):
            try:
                await ws.send_str(self._config_message)
                return await self._get_playable_items(ws)
            except ClientError as err:
                msg = 'unable to obtain playable items'
                raise YaynisonError(msg) from err

    async def _obtain_ticket(self, ws: ClientWebSocketResponse) -> None:
        message = orjson.loads(await ws.receive_str())

        if 'error' in message:
            msg = 'got an error in ticket logic'
            raise YaynisonError(msg)

        self._connection_uri = f'wss://{message["host"]}/ynison_state.YnisonStateService/PutYnisonState'
        self._redirect_ticket = message['redirect_ticket']
        self._session_id = message['session_id']

    @staticmethod
    async def _get_playable_items(ws: ClientWebSocketResponse) -> list[YanisonPlayableItem]:
        playable = []

        message = orjson.loads(await ws.receive_str())
        player_queue = message.get('player_state', {}).get('player_queue', {})
        current_index = player_queue.get('current_playable_index', 0)
        playable_list = player_queue.get('playable_list', [])

        # note: + 1 because iteration starts from 0 yk
        for it in reversed(playable_list[: (current_index + 1)]):
            if it['playable_type'] != 'TRACK':
                continue

            playable.append(
                YanisonPlayableItem(
                    playable_id=it['playable_id'],
                    album_id=it.get('album_id_optional', None),
                    from_item=it['from'],
                    title=it['title'],
                )
            )

        return playable

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
    def _headers(self) -> dict[str, str]:
        return {
            'Origin': 'https://music.yandex.ru',
            'Authorization': f'OAuth {self._token}',
            'Sec-Websocket-Protocol': f'Bearer, v2, {self._ticket_subprotocol}',
        }
