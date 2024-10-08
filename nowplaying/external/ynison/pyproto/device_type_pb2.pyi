from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNSPECIFIED: _ClassVar[DeviceType]
    WEB: _ClassVar[DeviceType]
    ANDROID: _ClassVar[DeviceType]
    IOS: _ClassVar[DeviceType]
    SMART_SPEAKER: _ClassVar[DeviceType]
    WEB_TV: _ClassVar[DeviceType]
    ANDROID_TV: _ClassVar[DeviceType]
    APPLE_TV: _ClassVar[DeviceType]

UNSPECIFIED: DeviceType
WEB: DeviceType
ANDROID: DeviceType
IOS: DeviceType
SMART_SPEAKER: DeviceType
WEB_TV: DeviceType
ANDROID_TV: DeviceType
APPLE_TV: DeviceType
