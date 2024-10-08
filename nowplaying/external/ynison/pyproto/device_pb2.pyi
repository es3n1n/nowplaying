from . import update_version_pb2 as _update_version_pb2
from . import device_type_pb2 as _device_type_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Device(_message.Message):
    __slots__ = ('info', 'volume', 'capabilities', 'session', 'is_offline', 'volume_info')
    INFO_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    IS_OFFLINE_FIELD_NUMBER: _ClassVar[int]
    VOLUME_INFO_FIELD_NUMBER: _ClassVar[int]
    info: DeviceInfo
    volume: float
    capabilities: DeviceCapabilities
    session: Session
    is_offline: bool
    volume_info: DeviceVolume
    def __init__(
        self,
        info: _Optional[_Union[DeviceInfo, _Mapping]] = ...,
        volume: _Optional[float] = ...,
        capabilities: _Optional[_Union[DeviceCapabilities, _Mapping]] = ...,
        session: _Optional[_Union[Session, _Mapping]] = ...,
        is_offline: bool = ...,
        volume_info: _Optional[_Union[DeviceVolume, _Mapping]] = ...,
    ) -> None: ...

class DeviceVolume(_message.Message):
    __slots__ = ('volume', 'version')
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    volume: float
    version: _update_version_pb2.UpdateVersion
    def __init__(
        self,
        volume: _Optional[float] = ...,
        version: _Optional[_Union[_update_version_pb2.UpdateVersion, _Mapping]] = ...,
    ) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ('device_id', 'title', 'type', 'app_name', 'app_version')
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    title: str
    type: _device_type_pb2.DeviceType
    app_name: str
    app_version: str
    def __init__(
        self,
        device_id: _Optional[str] = ...,
        title: _Optional[str] = ...,
        type: _Optional[_Union[_device_type_pb2.DeviceType, str]] = ...,
        app_name: _Optional[str] = ...,
        app_version: _Optional[str] = ...,
    ) -> None: ...

class DeviceCapabilities(_message.Message):
    __slots__ = ('can_be_player', 'can_be_remote_controller', 'volume_granularity')
    CAN_BE_PLAYER_FIELD_NUMBER: _ClassVar[int]
    CAN_BE_REMOTE_CONTROLLER_FIELD_NUMBER: _ClassVar[int]
    VOLUME_GRANULARITY_FIELD_NUMBER: _ClassVar[int]
    can_be_player: bool
    can_be_remote_controller: bool
    volume_granularity: int
    def __init__(
        self, can_be_player: bool = ..., can_be_remote_controller: bool = ..., volume_granularity: _Optional[int] = ...
    ) -> None: ...

class Session(_message.Message):
    __slots__ = ('id',)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...
