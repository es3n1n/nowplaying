# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: device_info_header.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC, 5, 27, 2, '', 'device_info_header.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import device_type_pb2 as device__type__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x18\x64\x65vice_info_header.proto\x12\rynison_header\x1a\x11\x64\x65vice_type.proto"g\n\x16YnisonDeviceInfoHeader\x12&\n\x04type\x18\x01 \x01(\x0e\x32\x18.ynison_state.DeviceType\x12\x10\n\x08\x61pp_name\x18\x02 \x01(\t\x12\x13\n\x0b\x61pp_version\x18\x03 \x01(\tBh\n\x1f\x63om.yandex.media.ynison.serviceP\x01ZCa.yandex-team.ru/music/backend/music-ynison/main/proto/ynisonheaderb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'device_info_header_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals[
        'DESCRIPTOR'
    ]._serialized_options = b'\n\037com.yandex.media.ynison.serviceP\001ZCa.yandex-team.ru/music/backend/music-ynison/main/proto/ynisonheader'
    _globals['_YNISONDEVICEINFOHEADER']._serialized_start = 62
    _globals['_YNISONDEVICEINFOHEADER']._serialized_end = 165
# @@protoc_insertion_point(module_scope)