from . import update_version_pb2 as _update_version_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PlayingStatus(_message.Message):
    __slots__ = ('progress_ms', 'duration_ms', 'paused', 'playback_speed', 'version')
    PROGRESS_MS_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    PLAYBACK_SPEED_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    progress_ms: int
    duration_ms: int
    paused: bool
    playback_speed: float
    version: _update_version_pb2.UpdateVersion
    def __init__(
        self,
        progress_ms: _Optional[int] = ...,
        duration_ms: _Optional[int] = ...,
        paused: bool = ...,
        playback_speed: _Optional[float] = ...,
        version: _Optional[_Union[_update_version_pb2.UpdateVersion, _Mapping]] = ...,
    ) -> None: ...
