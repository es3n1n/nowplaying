# Ported from https://github.com/bulatorr/go-yaynison/
from dataclasses import dataclass
from typing import List

from orjson import dumps, loads
from websockets import WebSocketClientProtocol, connect, headers
from websockets.exceptions import WebSocketException


def do_nothing(*args, **kwargs) -> None:
    return None


# Workaround for ticket's json subprotocol
headers.validate_subprotocols.__code__ = do_nothing.__code__


class YaynisonException(Exception):
    pass


@dataclass
class YanisonPlayableItem:
    playable_id: str
    album_id: str | None
    from_item: str
    title: str  # might be empty, not sure why


class Yaynison:
    def __init__(self, token: str):
        self.token = token
        self.device = 'playinnowbot'
        self.headers = [
            ('Origin', 'https://music.yandex.ru'),
            ('Authorization', f'OAuth {self.token}')
        ]

        self.connection_uri: str | None = None
        self.redirect_ticket: str | None = None
        self.session_id: str | None = None

        self.config_message: str = dumps({
            'update_full_state': {
                'player_state': {
                    'player_queue': {
                        'current_playable_index': -1,
                        'entity_id': '',
                        'entity_type': 'VARIOUS',
                        'playable_list': [],
                        'options': {'repeat_mode': 'NONE'},
                        'entity_context': 'BASED_ON_ENTITY_BY_DEFAULT',
                        'version': {'device_id': self.device,
                                    'version': 9021243204784341000,
                                    'timestamp_ms': 0},
                        'from_optional': ''
                    },
                    'status': {
                        'duration_ms': 0,
                        'paused': True,
                        'playback_speed': 1,
                        'progress_ms': 0,
                        'version': {
                            'device_id': self.device,
                            'version': 8321822175199937000,
                            'timestamp_ms': 0
                        }
                    }
                },
                'device': {
                    'capabilities': {
                        'can_be_player': False,
                        'can_be_remote_controller': False,
                        'volume_granularity': 0
                    },
                    'info': {
                        'device_id': self.device,
                        'type': 'WEB',
                        'title': 'playinnowbot',
                        'app_name': 'Chrome'
                    },
                    'volume_info': {'volume': 0},
                    'is_shadow': True
                },
                'is_currently_active': False
            },
            'rid': 'ac281c26-a047-4419-ad00-e4fbfda1cba3',
            'player_action_timestamp_ms': 0,
            'activity_interception_type': 'DO_NOT_INTERCEPT_BY_DEFAULT'
        }).decode()

        self.conn: WebSocketClientProtocol | None = None

    async def startup(self):
        await self.get_ticket()
        await self.connect()

    @property
    def _ticket_subprotocol(self) -> str:
        data = {
            'Ynison-Device-Id': self.device,
            'Ynison-Device-Info': '{"app_name":"Chrome","type":1}'
        }

        if self.redirect_ticket is not None:
            data['Ynison-Redirect-Ticket'] = self.redirect_ticket

        if self.session_id is not None:
            data['Ynison-Session-Id'] = self.session_id

        return dumps(data).decode()

    @property
    def _subprotocols(self) -> List[str]:
        return ['Bearer', 'v2', self._ticket_subprotocol]

    async def get_ticket(self) -> None:
        try:
            conn = await connect(
                'wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison',
                extra_headers=self.headers,
                subprotocols=self._subprotocols,  # type: ignore
                compression=None,
            )

            message = loads(await conn.recv())
            await conn.close()
            if 'error' in message:
                raise YaynisonException('got an error in ticket logic')

            self.connection_uri = f'wss://{message["host"]}/ynison_state.YnisonStateService/PutYnisonState'
            self.redirect_ticket = message['redirect_ticket']
            self.session_id = message['session_id']
        except WebSocketException:
            raise YaynisonException('unable to get the ticket')

    async def disconnect(self) -> None:
        if self.conn is None:
            return

        await self.conn.close()

    async def connect(self) -> None:
        if self.connection_uri is None:
            await self.get_ticket()
            assert self.connection_uri is not None

        try:
            self.conn = await connect(
                self.connection_uri,
                extra_headers=self.headers,
                subprotocols=self._subprotocols,  # type: ignore
                compression=None,
            )
            await self.conn.send(self.config_message)
        except WebSocketException:
            await self.disconnect()
            raise YaynisonException('unable to connect to yaynison')

    async def get_playable_items(self) -> List[YanisonPlayableItem]:
        if self.conn is None:
            await self.connect()
            assert self.conn is not None

        result = list()

        m = loads(await self.conn.recv())
        player_queue = m.get('player_state', {}).get('player_queue', {})
        current_index = player_queue.get('current_playable_index', 0)

        for it in player_queue.get('playable_list', [])[current_index:]:
            if it['playable_type'] != 'TRACK':
                continue

            result.append(YanisonPlayableItem(
                playable_id=it['playable_id'],
                album_id=it.get('album_id_optional', None),
                from_item=it['from'],
                title=it['title']
            ))

        return result

    async def one_shot_playable_items(self) -> List[YanisonPlayableItem]:
        await self.startup()
        result = await self.get_playable_items()
        await self.disconnect()
        return result
