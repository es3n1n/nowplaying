from dataclasses import dataclass
from enum import IntEnum, auto, unique
from pathlib import Path
from secrets import randbits
from time import time
from typing import cast

import certifi
from grpc import ssl_channel_credentials
from grpc.aio import Channel, insecure_channel, secure_channel

from nowplaying.core.config import config
from nowplaying.util.dns import select_hostname

from .pyproto.device_pb2 import DeviceCapabilities, DeviceInfo
from .pyproto.device_type_pb2 import DeviceType
from .pyproto.playable_pb2 import Playable
from .pyproto.player_state_pb2 import PlayerState
from .pyproto.playing_status_pb2 import PlayingStatus
from .pyproto.queue_pb2 import PlayerQueue, PlayerStateOptions
from .pyproto.update_version_pb2 import UpdateVersion
from .pyproto.ynison_redirector_service_pb2 import RedirectRequest, RedirectResponse
from .pyproto.ynison_redirector_service_pb2_grpc import YnisonRedirectServiceStub
from .pyproto.ynison_state_pb2 import (
    PutYnisonStateRequest,
    PutYnisonStateResponse,
    UpdateDevice,
    UpdateFullState,
    UpdatePlayerState,
)
from .pyproto.ynison_state_pb2_grpc import YnisonStateServiceStub


ssl_credentials = ssl_channel_credentials(Path(certifi.where()).read_bytes())
grpc_proxy_endpoint = select_hostname(config.YANDEX_GRPC_PROXY_DOCKER_HOST, config.YANDEX_GRPC_PROXY_HOST)


class YnisonError(Exception):
    """Ynison base error class."""


class YnisonClientSideError(YnisonError):
    """Ynison client side error that will be thrown whenever user is doing something wrong."""


@dataclass
class YnisonPlayableItem:
    playable_id: str
    album_id: str | None
    title: str  # might be empty
    currently_playing: bool


@unique
class EInsertMode(IntEnum):
    # Play right now
    OVERRIDE = auto()
    # Enqueue as next track
    ENQUEUE = auto()
    # Enqueue as next track and immediately skip to it
    ENQUEUE_AND_SKIP = auto()


class Ynison:
    def __init__(self, token: str, device_id: str = 'playinnowbot', app_title: str = 'playinnowbot') -> None:
        self._token = token
        self._app_title = app_title
        self._device_id = device_id
        self._header: list[tuple[str, str]] = [
            ('authorization', f'OAuth {token}'),
            ('ynison-device-id', self._device_id),
        ]
        self._host: str | None = None

    async def _get_ticket(self) -> None:
        if self._host:
            return

        async with secure_channel('ynison.music.yandex.net:443', ssl_credentials) as channel:
            svc = YnisonRedirectServiceStub(channel)
            result: RedirectResponse = await svc.GetRedirectToYnison(RedirectRequest(), metadata=self._header)

            self._host = result.host
            self._header.append(('ynison-redirect-ticket', result.redirect_ticket))
            self._header.append(('ynison-session-id', str(result.session_id)))
            self._header.append(('x-proxy-host', self._host))

    @property
    def _channel(self) -> Channel:
        return insecure_channel(f'{grpc_proxy_endpoint}:{config.YANDEX_GRPC_PROXY_PORT}')

    async def _exchange(
        self, svc: YnisonStateServiceStub, msg: PutYnisonStateRequest, *, ensure_returned: bool = True
    ) -> PutYnisonStateResponse | None:
        async for received in svc.PutYnisonState(iter((msg,)), metadata=self._header, timeout=30):
            return received

        if ensure_returned:
            err_msg = 'We should not be here'
            raise ValueError(err_msg)

        return None

    async def _negotiate(self, svc: YnisonStateServiceStub) -> PutYnisonStateResponse:
        result = await self._exchange(
            svc,
            PutYnisonStateRequest(
                update_full_state=UpdateFullState(
                    player_state=PlayerState(  # this state doesn't really matter
                        status=PlayingStatus(paused=True, playback_speed=1),
                        player_queue=PlayerQueue(
                            current_playable_index=-1,
                            entity_type=PlayerQueue.EntityType.VARIOUS,
                            options=PlayerStateOptions(repeat_mode=PlayerStateOptions.NONE),
                            entity_context=PlayerQueue.EntityContext.BASED_ON_ENTITY_BY_DEFAULT,
                        ),
                    ),
                    device=UpdateDevice(
                        info=DeviceInfo(
                            device_id=self._device_id,
                            type=DeviceType.WEB,
                            title=self._app_title,
                            app_name='Chrome',
                        ),
                        capabilities=DeviceCapabilities(
                            can_be_player=False,
                            can_be_remote_controller=True,
                        ),
                    ),
                )
            ),
        )
        return cast(PutYnisonStateResponse, result)

    @staticmethod
    def _get_playable_items(msg: PutYnisonStateResponse, *, from_current_to_prev: bool) -> list[YnisonPlayableItem]:
        playable = []

        player_queue = msg.player_state.player_queue
        current_index = player_queue.current_playable_index
        playable_list = player_queue.playable_list

        iterator = reversed(playable_list[: (current_index + 1)]) if from_current_to_prev else iter(playable_list)
        current_local_index = 0 if from_current_to_prev else current_index

        for i, it in enumerate(iterator):
            if it.playable_type != Playable.PlayableType.TRACK:
                continue

            playable.append(
                YnisonPlayableItem(
                    playable_id=it.playable_id,
                    album_id=it.album_id_optional.value if it.album_id_optional is not None else None,
                    title=it.title,
                    currently_playing=i == current_local_index,
                )
            )

        return playable

    async def get_playable_items(self, *, from_current_to_prev: bool = False) -> list[YnisonPlayableItem]:
        await self._get_ticket()
        async with self._channel as channel:
            result = await self._negotiate(YnisonStateServiceStub(channel))
            return self._get_playable_items(result, from_current_to_prev=from_current_to_prev)

    @property
    def _version(self) -> UpdateVersion:
        return UpdateVersion(
            device_id=self._device_id,
            version=randbits(32),
            timestamp_ms=int(time() * 1000),
        )

    async def _insert_to_player_queue(
        self,
        svc: YnisonStateServiceStub,
        response: PutYnisonStateResponse,
        track_id: str,
        insert_mode: EInsertMode,
    ) -> None:
        player_state = response.player_state
        player_queue = player_state.player_queue
        player_status = player_state.status
        current_playable_index = player_queue.current_playable_index

        playable_list = player_queue.playable_list

        # Radio will re-generate the queue each skip,
        # doesnt matter whether we add our track, it won't be played anyways.
        # Although we can override the currently playing track with no issues.
        if insert_mode == EInsertMode.ENQUEUE and player_queue.entity_type == PlayerQueue.EntityType.RADIO:
            msg = 'Enqueueing to radio queue is unsupported'
            raise YnisonClientSideError(msg)

        track_item = Playable(
            playable_id=track_id,
            playable_type=Playable.PlayableType.TRACK,
        )

        match insert_mode:
            case EInsertMode.ENQUEUE:
                playable_list.insert(current_playable_index + 1, track_item)
            case EInsertMode.ENQUEUE_AND_SKIP:
                playable_list.insert(current_playable_index + 1, track_item)
                current_playable_index += 1
            case EInsertMode.OVERRIDE:
                playable_list = [track_item]

        await self._exchange(
            svc,
            PutYnisonStateRequest(
                update_player_state=UpdatePlayerState(
                    player_state=PlayerState(
                        status=PlayingStatus(
                            progress_ms=player_status.progress_ms if insert_mode == EInsertMode.ENQUEUE else 0,
                            duration_ms=player_status.duration_ms if insert_mode == EInsertMode.ENQUEUE else None,
                            paused=player_status.paused,
                            playback_speed=player_status.playback_speed,
                        ),
                        player_queue=PlayerQueue(
                            entity_id=player_queue.entity_id,
                            entity_type=player_queue.entity_type,
                            queue=player_queue.queue,
                            current_playable_index=current_playable_index,
                            playable_list=playable_list,
                            options=PlayerStateOptions(repeat_mode=player_queue.options.repeat_mode),
                        ),
                    )
                )
            ),
            ensure_returned=False,
        )

    async def add_to_queue(self, track_id: str) -> None:
        await self._get_ticket()
        async with self._channel as channel:
            svc = YnisonStateServiceStub(channel)
            response = await self._negotiate(svc)
            await self._insert_to_player_queue(svc, response, track_id, EInsertMode.ENQUEUE)

    async def play_track(self, track_id: str, *, keep_queue: bool = False) -> None:
        await self._get_ticket()
        async with self._channel as channel:
            svc = YnisonStateServiceStub(channel)
            response = await self._negotiate(svc)

            if keep_queue:
                # Add item to queue and skip to it so that the queue won't be empty
                return await self._insert_to_player_queue(svc, response, track_id, EInsertMode.ENQUEUE_AND_SKIP)

            # Overriding the queue to our own with only one track entry
            return await self._insert_to_player_queue(svc, response, track_id, EInsertMode.OVERRIDE)
