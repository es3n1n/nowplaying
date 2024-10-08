from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RedirectRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RedirectResponse(_message.Message):
    __slots__ = ('host', 'redirect_ticket', 'session_id', 'keep_alive_params')
    HOST_FIELD_NUMBER: _ClassVar[int]
    REDIRECT_TICKET_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_PARAMS_FIELD_NUMBER: _ClassVar[int]
    host: str
    redirect_ticket: str
    session_id: int
    keep_alive_params: KeepAliveParams
    def __init__(
        self,
        host: _Optional[str] = ...,
        redirect_ticket: _Optional[str] = ...,
        session_id: _Optional[int] = ...,
        keep_alive_params: _Optional[_Union[KeepAliveParams, _Mapping]] = ...,
    ) -> None: ...

class KeepAliveParams(_message.Message):
    __slots__ = ('keep_alive_time_seconds', 'keep_alive_timeout_seconds')
    KEEP_ALIVE_TIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    KEEP_ALIVE_TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    keep_alive_time_seconds: int
    keep_alive_timeout_seconds: int
    def __init__(
        self, keep_alive_time_seconds: _Optional[int] = ..., keep_alive_timeout_seconds: _Optional[int] = ...
    ) -> None: ...
