from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class UpdateVersion(_message.Message):
    __slots__ = ('device_id', 'version', 'timestamp_ms')
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    version: int
    timestamp_ms: int
    def __init__(
        self, device_id: _Optional[str] = ..., version: _Optional[int] = ..., timestamp_ms: _Optional[int] = ...
    ) -> None: ...
