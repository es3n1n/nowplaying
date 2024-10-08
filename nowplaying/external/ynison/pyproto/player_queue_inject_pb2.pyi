from . import update_version_pb2 as _update_version_pb2
from . import playing_status_pb2 as _playing_status_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PlayerQueueInject(_message.Message):
    __slots__ = ('playing_status', 'playable', 'version')
    class Playable(_message.Message):
        __slots__ = ('playable_id', 'playable_type', 'title', 'cover_url')
        class PlayableType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            UNSPECIFIED: _ClassVar[PlayerQueueInject.Playable.PlayableType]
            ALICE_SHOT: _ClassVar[PlayerQueueInject.Playable.PlayableType]
            AD: _ClassVar[PlayerQueueInject.Playable.PlayableType]
            PREROLL: _ClassVar[PlayerQueueInject.Playable.PlayableType]

        UNSPECIFIED: PlayerQueueInject.Playable.PlayableType
        ALICE_SHOT: PlayerQueueInject.Playable.PlayableType
        AD: PlayerQueueInject.Playable.PlayableType
        PREROLL: PlayerQueueInject.Playable.PlayableType
        PLAYABLE_ID_FIELD_NUMBER: _ClassVar[int]
        PLAYABLE_TYPE_FIELD_NUMBER: _ClassVar[int]
        TITLE_FIELD_NUMBER: _ClassVar[int]
        COVER_URL_FIELD_NUMBER: _ClassVar[int]
        playable_id: str
        playable_type: PlayerQueueInject.Playable.PlayableType
        title: str
        cover_url: _wrappers_pb2.StringValue
        def __init__(
            self,
            playable_id: _Optional[str] = ...,
            playable_type: _Optional[_Union[PlayerQueueInject.Playable.PlayableType, str]] = ...,
            title: _Optional[str] = ...,
            cover_url: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
        ) -> None: ...

    PLAYING_STATUS_FIELD_NUMBER: _ClassVar[int]
    PLAYABLE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    playing_status: _playing_status_pb2.PlayingStatus
    playable: PlayerQueueInject.Playable
    version: _update_version_pb2.UpdateVersion
    def __init__(
        self,
        playing_status: _Optional[_Union[_playing_status_pb2.PlayingStatus, _Mapping]] = ...,
        playable: _Optional[_Union[PlayerQueueInject.Playable, _Mapping]] = ...,
        version: _Optional[_Union[_update_version_pb2.UpdateVersion, _Mapping]] = ...,
    ) -> None: ...
