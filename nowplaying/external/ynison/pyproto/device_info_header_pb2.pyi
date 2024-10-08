from . import device_type_pb2 as _device_type_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class YnisonDeviceInfoHeader(_message.Message):
    __slots__ = ('type', 'app_name', 'app_version')
    TYPE_FIELD_NUMBER: _ClassVar[int]
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    type: _device_type_pb2.DeviceType
    app_name: str
    app_version: str
    def __init__(
        self,
        type: _Optional[_Union[_device_type_pb2.DeviceType, str]] = ...,
        app_name: _Optional[str] = ...,
        app_version: _Optional[str] = ...,
    ) -> None: ...
