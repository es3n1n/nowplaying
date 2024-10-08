from . import queue_pb2 as _queue_pb2
from . import player_queue_inject_pb2 as _player_queue_inject_pb2
from . import playing_status_pb2 as _playing_status_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PlayerState(_message.Message):
    __slots__ = ('status', 'player_queue', 'player_queue_inject_optional')
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PLAYER_QUEUE_FIELD_NUMBER: _ClassVar[int]
    PLAYER_QUEUE_INJECT_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    status: _playing_status_pb2.PlayingStatus
    player_queue: _queue_pb2.PlayerQueue
    player_queue_inject_optional: _player_queue_inject_pb2.PlayerQueueInject
    def __init__(
        self,
        status: _Optional[_Union[_playing_status_pb2.PlayingStatus, _Mapping]] = ...,
        player_queue: _Optional[_Union[_queue_pb2.PlayerQueue, _Mapping]] = ...,
        player_queue_inject_optional: _Optional[_Union[_player_queue_inject_pb2.PlayerQueueInject, _Mapping]] = ...,
    ) -> None: ...
