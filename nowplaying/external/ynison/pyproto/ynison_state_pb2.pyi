from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.api import annotations_pb2 as _annotations_pb2
from . import device_pb2 as _device_pb2
from . import player_state_pb2 as _player_state_pb2
from . import player_queue_inject_pb2 as _player_queue_inject_pb2
from . import playing_status_pb2 as _playing_status_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class PutYnisonStateRequest(_message.Message):
    __slots__ = (
        'update_full_state',
        'update_active_device',
        'update_playing_status',
        'update_player_state',
        'update_volume',
        'update_player_queue_inject',
        'update_session_params',
        'update_volume_info',
        'sync_state_from_eov',
        'player_action_timestamp_ms',
        'rid',
        'activity_interception_type',
    )
    class ActivityInterceptionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DO_NOT_INTERCEPT_BY_DEFAULT: _ClassVar[PutYnisonStateRequest.ActivityInterceptionType]
        INTERCEPT_IF_NO_ONE_ACTIVE: _ClassVar[PutYnisonStateRequest.ActivityInterceptionType]
        INTERCEPT_EAGER: _ClassVar[PutYnisonStateRequest.ActivityInterceptionType]

    DO_NOT_INTERCEPT_BY_DEFAULT: PutYnisonStateRequest.ActivityInterceptionType
    INTERCEPT_IF_NO_ONE_ACTIVE: PutYnisonStateRequest.ActivityInterceptionType
    INTERCEPT_EAGER: PutYnisonStateRequest.ActivityInterceptionType
    UPDATE_FULL_STATE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_ACTIVE_DEVICE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_PLAYING_STATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_PLAYER_STATE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_VOLUME_FIELD_NUMBER: _ClassVar[int]
    UPDATE_PLAYER_QUEUE_INJECT_FIELD_NUMBER: _ClassVar[int]
    UPDATE_SESSION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_VOLUME_INFO_FIELD_NUMBER: _ClassVar[int]
    SYNC_STATE_FROM_EOV_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ACTION_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    RID_FIELD_NUMBER: _ClassVar[int]
    ACTIVITY_INTERCEPTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    update_full_state: UpdateFullState
    update_active_device: UpdateActiveDevice
    update_playing_status: UpdatePlayingStatus
    update_player_state: UpdatePlayerState
    update_volume: UpdateVolume
    update_player_queue_inject: UpdatePlayerQueueInject
    update_session_params: UpdateSessionParams
    update_volume_info: UpdateVolumeInfo
    sync_state_from_eov: SyncStateFromEOV
    player_action_timestamp_ms: int
    rid: str
    activity_interception_type: PutYnisonStateRequest.ActivityInterceptionType
    def __init__(
        self,
        update_full_state: _Optional[_Union[UpdateFullState, _Mapping]] = ...,
        update_active_device: _Optional[_Union[UpdateActiveDevice, _Mapping]] = ...,
        update_playing_status: _Optional[_Union[UpdatePlayingStatus, _Mapping]] = ...,
        update_player_state: _Optional[_Union[UpdatePlayerState, _Mapping]] = ...,
        update_volume: _Optional[_Union[UpdateVolume, _Mapping]] = ...,
        update_player_queue_inject: _Optional[_Union[UpdatePlayerQueueInject, _Mapping]] = ...,
        update_session_params: _Optional[_Union[UpdateSessionParams, _Mapping]] = ...,
        update_volume_info: _Optional[_Union[UpdateVolumeInfo, _Mapping]] = ...,
        sync_state_from_eov: _Optional[_Union[SyncStateFromEOV, _Mapping]] = ...,
        player_action_timestamp_ms: _Optional[int] = ...,
        rid: _Optional[str] = ...,
        activity_interception_type: _Optional[_Union[PutYnisonStateRequest.ActivityInterceptionType, str]] = ...,
    ) -> None: ...

class PutYnisonStateResponse(_message.Message):
    __slots__ = ('player_state', 'devices', 'active_device_id_optional', 'timestamp_ms', 'rid')
    PLAYER_STATE_FIELD_NUMBER: _ClassVar[int]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_DEVICE_ID_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    RID_FIELD_NUMBER: _ClassVar[int]
    player_state: _player_state_pb2.PlayerState
    devices: _containers.RepeatedCompositeFieldContainer[_device_pb2.Device]
    active_device_id_optional: _wrappers_pb2.StringValue
    timestamp_ms: int
    rid: str
    def __init__(
        self,
        player_state: _Optional[_Union[_player_state_pb2.PlayerState, _Mapping]] = ...,
        devices: _Optional[_Iterable[_Union[_device_pb2.Device, _Mapping]]] = ...,
        active_device_id_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
        timestamp_ms: _Optional[int] = ...,
        rid: _Optional[str] = ...,
    ) -> None: ...

class UpdatePlayerQueueInject(_message.Message):
    __slots__ = ('player_queue_inject',)
    PLAYER_QUEUE_INJECT_FIELD_NUMBER: _ClassVar[int]
    player_queue_inject: _player_queue_inject_pb2.PlayerQueueInject
    def __init__(
        self, player_queue_inject: _Optional[_Union[_player_queue_inject_pb2.PlayerQueueInject, _Mapping]] = ...
    ) -> None: ...

class UpdateActiveDevice(_message.Message):
    __slots__ = ('device_id_optional',)
    DEVICE_ID_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    device_id_optional: _wrappers_pb2.StringValue
    def __init__(self, device_id_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...) -> None: ...

class UpdatePlayingStatus(_message.Message):
    __slots__ = ('playing_status',)
    PLAYING_STATUS_FIELD_NUMBER: _ClassVar[int]
    playing_status: _playing_status_pb2.PlayingStatus
    def __init__(
        self, playing_status: _Optional[_Union[_playing_status_pb2.PlayingStatus, _Mapping]] = ...
    ) -> None: ...

class UpdateVolume(_message.Message):
    __slots__ = ('volume', 'device_id')
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    volume: float
    device_id: str
    def __init__(self, volume: _Optional[float] = ..., device_id: _Optional[str] = ...) -> None: ...

class UpdateVolumeInfo(_message.Message):
    __slots__ = ('device_id', 'volume_info')
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    VOLUME_INFO_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    volume_info: _device_pb2.DeviceVolume
    def __init__(
        self, device_id: _Optional[str] = ..., volume_info: _Optional[_Union[_device_pb2.DeviceVolume, _Mapping]] = ...
    ) -> None: ...

class UpdatePlayerState(_message.Message):
    __slots__ = ('player_state',)
    PLAYER_STATE_FIELD_NUMBER: _ClassVar[int]
    player_state: _player_state_pb2.PlayerState
    def __init__(self, player_state: _Optional[_Union[_player_state_pb2.PlayerState, _Mapping]] = ...) -> None: ...

class UpdateFullState(_message.Message):
    __slots__ = ('player_state', 'is_currently_active', 'device', 'sync_state_from_eov_optional')
    PLAYER_STATE_FIELD_NUMBER: _ClassVar[int]
    IS_CURRENTLY_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    SYNC_STATE_FROM_EOV_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    player_state: _player_state_pb2.PlayerState
    is_currently_active: bool
    device: UpdateDevice
    sync_state_from_eov_optional: SyncStateFromEOV
    def __init__(
        self,
        player_state: _Optional[_Union[_player_state_pb2.PlayerState, _Mapping]] = ...,
        is_currently_active: bool = ...,
        device: _Optional[_Union[UpdateDevice, _Mapping]] = ...,
        sync_state_from_eov_optional: _Optional[_Union[SyncStateFromEOV, _Mapping]] = ...,
    ) -> None: ...

class UpdateSessionParams(_message.Message):
    __slots__ = ('mute_events_if_passive',)
    MUTE_EVENTS_IF_PASSIVE_FIELD_NUMBER: _ClassVar[int]
    mute_events_if_passive: bool
    def __init__(self, mute_events_if_passive: bool = ...) -> None: ...

class UpdateDevice(_message.Message):
    __slots__ = ('info', 'volume', 'capabilities', 'volume_info')
    INFO_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    VOLUME_INFO_FIELD_NUMBER: _ClassVar[int]
    info: _device_pb2.DeviceInfo
    volume: float
    capabilities: _device_pb2.DeviceCapabilities
    volume_info: _device_pb2.DeviceVolume
    def __init__(
        self,
        info: _Optional[_Union[_device_pb2.DeviceInfo, _Mapping]] = ...,
        volume: _Optional[float] = ...,
        capabilities: _Optional[_Union[_device_pb2.DeviceCapabilities, _Mapping]] = ...,
        volume_info: _Optional[_Union[_device_pb2.DeviceVolume, _Mapping]] = ...,
    ) -> None: ...

class SyncStateFromEOV(_message.Message):
    __slots__ = ('actual_queue_id',)
    ACTUAL_QUEUE_ID_FIELD_NUMBER: _ClassVar[int]
    actual_queue_id: str
    def __init__(self, actual_queue_id: _Optional[str] = ...) -> None: ...
