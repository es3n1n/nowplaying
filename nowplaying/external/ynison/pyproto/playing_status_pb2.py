# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: playing_status.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 27, 2, '', 'playing_status.proto')
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import update_version_pb2 as update__version__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x14playing_status.proto\x12\x0cynison_state\x1a\x14update_version.proto"\x8f\x01\n\rPlayingStatus\x12\x13\n\x0bprogress_ms\x18\x01 \x01(\x03\x12\x13\n\x0b\x64uration_ms\x18\x02 \x01(\x03\x12\x0e\n\x06paused\x18\x03 \x01(\x08\x12\x16\n\x0eplayback_speed\x18\x04 \x01(\x01\x12,\n\x07version\x18\x05 \x01(\x0b\x32\x1b.ynison_state.UpdateVersionBg\n\x1f\x63om.yandex.media.ynison.serviceP\x01ZBa.yandex-team.ru/music/backend/music-ynison/main/proto/ynisonstateb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'playing_status_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals[
        'DESCRIPTOR'
    ]._serialized_options = b'\n\037com.yandex.media.ynison.serviceP\001ZBa.yandex-team.ru/music/backend/music-ynison/main/proto/ynisonstate'
    _globals['_PLAYINGSTATUS']._serialized_start = 61
    _globals['_PLAYINGSTATUS']._serialized_end = 204
# @@protoc_insertion_point(module_scope)
