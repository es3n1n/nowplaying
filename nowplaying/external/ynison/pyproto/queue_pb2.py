# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: queue.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 27, 2, '', 'queue.proto')
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import playable_pb2 as playable__pb2
from . import update_version_pb2 as update__version__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0bqueue.proto\x12\x0cynison_state\x1a\x0eplayable.proto\x1a\x14update_version.proto\x1a\x1egoogle/protobuf/wrappers.proto"\xcd\x16\n\x0bPlayerQueue\x12\x15\n\tentity_id\x18\x01 \x01(\tB\x02\x18\x01\x12=\n\x0b\x65ntity_type\x18\x02 \x01(\x0e\x32$.ynison_state.PlayerQueue.EntityTypeB\x02\x18\x01\x12.\n\x05queue\x18\x0c \x01(\x0b\x32\x1f.ynison_state.PlayerQueue.Queue\x12\x1e\n\x16\x63urrent_playable_index\x18\x03 \x01(\x05\x12-\n\rplayable_list\x18\x04 \x03(\x0b\x32\x16.ynison_state.Playable\x12\x31\n\x07options\x18\x05 \x01(\x0b\x32 .ynison_state.PlayerStateOptions\x12,\n\x07version\x18\x06 \x01(\x0b\x32\x1b.ynison_state.UpdateVersion\x12/\n\x10shuffle_optional\x18\x07 \x01(\x0b\x32\x15.ynison_state.Shuffle\x12\x43\n\x0e\x65ntity_context\x18\x08 \x01(\x0e\x32\'.ynison_state.PlayerQueue.EntityContextB\x02\x18\x01\x12\x33\n\rfrom_optional\x18\t \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12L\n\x17initial_entity_optional\x18\n \x01(\x0b\x32\'.ynison_state.PlayerQueue.InitialEntityB\x02\x18\x01\x12Q\n\x17\x61\x64\x64ing_options_optional\x18\x0b \x01(\x0b\x32,.ynison_state.PlayerQueue.PlayerQueueOptionsB\x02\x18\x01\x1a\xcd\x0c\n\x05Queue\x12?\n\nwave_queue\x18\x01 \x01(\x0b\x32).ynison_state.PlayerQueue.Queue.WaveQueueH\x00\x12K\n\x10generative_queue\x18\x02 \x01(\x0b\x32/.ynison_state.PlayerQueue.Queue.GenerativeQueueH\x00\x12\x46\n\x0e\x66m_radio_queue\x18\x03 \x01(\x0b\x32,.ynison_state.PlayerQueue.Queue.FmRadioQueueH\x00\x12J\n\x10video_wave_queue\x18\x04 \x01(\x0b\x32..ynison_state.PlayerQueue.Queue.VideoWaveQueueH\x00\x12N\n\x12local_tracks_queue\x18\x05 \x01(\x0b\x32\x30.ynison_state.PlayerQueue.Queue.LocalTracksQueueH\x00\x1a\xdc\x08\n\tWaveQueue\x12\x39\n\x19recommended_playable_list\x18\x01 \x03(\x0b\x32\x16.ynison_state.Playable\x12\x1b\n\x13live_playable_index\x18\x02 \x01(\x05\x12O\n\x0e\x65ntity_options\x18\x03 \x01(\x0b\x32\x37.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions\x1a\xa5\x07\n\rEntityOptions\x12\x61\n\x14wave_entity_optional\x18\x01 \x01(\x0b\x32\x43.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSession\x12\x61\n\rtrack_sources\x18\x02 \x03(\x0b\x32J.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.TrackSourceWithKey\x1a!\n\x0bWaveSession\x12\x12\n\nsession_id\x18\x01 \x01(\t\x1a\xf1\x01\n\x12TrackSourceWithKey\x12\x0b\n\x03key\x18\x01 \x01(\r\x12Y\n\x0bwave_source\x18\x02 \x01(\x0b\x32\x42.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSourceH\x00\x12\x63\n\x10phonoteka_source\x18\x03 \x01(\x0b\x32G.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.PhonotekaSourceH\x00\x42\x0e\n\x0ctrack_source\x1a\x0c\n\nWaveSource\x1a\xdf\x02\n\x0fPhonotekaSource\x12U\n\tartist_id\x18\x02 \x01(\x0b\x32@.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.ArtistIdH\x00\x12Y\n\x0bplaylist_id\x18\x03 \x01(\x0b\x32\x42.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.PlaylistIdH\x00\x12S\n\x08\x61lbum_id\x18\x04 \x01(\x0b\x32?.ynison_state.PlayerQueue.Queue.WaveQueue.EntityOptions.AlbumIdH\x00\x12?\n\x0e\x65ntity_context\x18\x01 \x01(\x0e\x32\'.ynison_state.PlayerQueue.EntityContextB\x04\n\x02id\x1a\x16\n\x08\x41rtistId\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x18\n\nPlaylistId\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x15\n\x07\x41lbumId\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x1d\n\x0fGenerativeQueue\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x1a\n\x0c\x46mRadioQueue\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x1c\n\x0eVideoWaveQueue\x12\n\n\x02id\x18\x01 \x01(\t\x1a\x12\n\x10LocalTracksQueueB\x06\n\x04type\x1a\x61\n\rInitialEntity\x12\x11\n\tentity_id\x18\x01 \x01(\t\x12\x39\n\x0b\x65ntity_type\x18\x02 \x01(\x0e\x32$.ynison_state.PlayerQueue.EntityType:\x02\x18\x01\x1a\x9b\x01\n\x12PlayerQueueOptions\x12R\n\rradio_options\x18\x01 \x01(\x0b\x32\x39.ynison_state.PlayerQueue.PlayerQueueOptions.RadioOptionsH\x00\x1a"\n\x0cRadioOptions\x12\x12\n\nsession_id\x18\x01 \x01(\t:\x02\x18\x01\x42\t\n\x07options"\x9e\x01\n\nEntityType\x12\x0f\n\x0bUNSPECIFIED\x10\x00\x12\n\n\x06\x41RTIST\x10\x01\x12\x0c\n\x08PLAYLIST\x10\x02\x12\t\n\x05\x41LBUM\x10\x03\x12\t\n\x05RADIO\x10\x04\x12\x0b\n\x07VARIOUS\x10\x05\x12\x0e\n\nGENERATIVE\x10\x06\x12\x0c\n\x08\x46M_RADIO\x10\x07\x12\x0e\n\nVIDEO_WAVE\x10\x08\x12\x10\n\x0cLOCAL_TRACKS\x10\t\x1a\x02\x18\x01"\xc9\x01\n\rEntityContext\x12\x1e\n\x1a\x42\x41SED_ON_ENTITY_BY_DEFAULT\x10\x00\x12\x0f\n\x0bUSER_TRACKS\x10\x01\x12\x15\n\x11\x44OWNLOADED_TRACKS\x10\x02\x12\n\n\x06SEARCH\x10\x03\x12\x11\n\rMUSIC_HISTORY\x10\x04\x12\x18\n\x14MUSIC_HISTORY_SEARCH\x10\x05\x12\x18\n\x14\x41RTIST_MY_COLLECTION\x10\x06\x12\x1d\n\x19\x41RTIST_FAMILIAR_FROM_WAVE\x10\x07"\x91\x01\n\x12PlayerStateOptions\x12@\n\x0brepeat_mode\x18\x01 \x01(\x0e\x32+.ynison_state.PlayerStateOptions.RepeatMode"9\n\nRepeatMode\x12\x0f\n\x0bUNSPECIFIED\x10\x00\x12\x08\n\x04NONE\x10\x01\x12\x07\n\x03ONE\x10\x02\x12\x07\n\x03\x41LL\x10\x03"#\n\x07Shuffle\x12\x18\n\x10playable_indices\x18\x01 \x03(\rBf\n\x1f\x63om.yandex.media.ynison.serviceP\x01ZAa.yandex-team.ru/music/backend/music-ynison/hub/proto/ynisonstateb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'queue_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals[
        'DESCRIPTOR'
    ]._serialized_options = (
        b'\n\037com.yandex.media.ynison.serviceP\001ZAa.yandex-team.ru/music/backend/music-ynison/hub/proto/ynisonstate'
    )
    _globals['_PLAYERQUEUE_INITIALENTITY']._loaded_options = None
    _globals['_PLAYERQUEUE_INITIALENTITY']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS']._loaded_options = None
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE_ENTITYTYPE']._loaded_options = None
    _globals['_PLAYERQUEUE_ENTITYTYPE']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE'].fields_by_name['entity_id']._loaded_options = None
    _globals['_PLAYERQUEUE'].fields_by_name['entity_id']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE'].fields_by_name['entity_type']._loaded_options = None
    _globals['_PLAYERQUEUE'].fields_by_name['entity_type']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE'].fields_by_name['entity_context']._loaded_options = None
    _globals['_PLAYERQUEUE'].fields_by_name['entity_context']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE'].fields_by_name['initial_entity_optional']._loaded_options = None
    _globals['_PLAYERQUEUE'].fields_by_name['initial_entity_optional']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE'].fields_by_name['adding_options_optional']._loaded_options = None
    _globals['_PLAYERQUEUE'].fields_by_name['adding_options_optional']._serialized_options = b'\030\001'
    _globals['_PLAYERQUEUE']._serialized_start = 100
    _globals['_PLAYERQUEUE']._serialized_end = 2993
    _globals['_PLAYERQUEUE_QUEUE']._serialized_start = 758
    _globals['_PLAYERQUEUE_QUEUE']._serialized_end = 2371
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE']._serialized_start = 1138
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE']._serialized_end = 2254
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS']._serialized_start = 1321
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS']._serialized_end = 2254
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_WAVESESSION']._serialized_start = 1536
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_WAVESESSION']._serialized_end = 1569
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_TRACKSOURCEWITHKEY']._serialized_start = 1572
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_TRACKSOURCEWITHKEY']._serialized_end = 1813
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_WAVESOURCE']._serialized_start = 1815
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_WAVESOURCE']._serialized_end = 1827
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_PHONOTEKASOURCE']._serialized_start = 1830
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_PHONOTEKASOURCE']._serialized_end = 2181
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_ARTISTID']._serialized_start = 2183
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_ARTISTID']._serialized_end = 2205
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_PLAYLISTID']._serialized_start = 2207
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_PLAYLISTID']._serialized_end = 2231
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_ALBUMID']._serialized_start = 2233
    _globals['_PLAYERQUEUE_QUEUE_WAVEQUEUE_ENTITYOPTIONS_ALBUMID']._serialized_end = 2254
    _globals['_PLAYERQUEUE_QUEUE_GENERATIVEQUEUE']._serialized_start = 2256
    _globals['_PLAYERQUEUE_QUEUE_GENERATIVEQUEUE']._serialized_end = 2285
    _globals['_PLAYERQUEUE_QUEUE_FMRADIOQUEUE']._serialized_start = 2287
    _globals['_PLAYERQUEUE_QUEUE_FMRADIOQUEUE']._serialized_end = 2313
    _globals['_PLAYERQUEUE_QUEUE_VIDEOWAVEQUEUE']._serialized_start = 2315
    _globals['_PLAYERQUEUE_QUEUE_VIDEOWAVEQUEUE']._serialized_end = 2343
    _globals['_PLAYERQUEUE_QUEUE_LOCALTRACKSQUEUE']._serialized_start = 2345
    _globals['_PLAYERQUEUE_QUEUE_LOCALTRACKSQUEUE']._serialized_end = 2363
    _globals['_PLAYERQUEUE_INITIALENTITY']._serialized_start = 2373
    _globals['_PLAYERQUEUE_INITIALENTITY']._serialized_end = 2470
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS']._serialized_start = 2473
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS']._serialized_end = 2628
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS_RADIOOPTIONS']._serialized_start = 2579
    _globals['_PLAYERQUEUE_PLAYERQUEUEOPTIONS_RADIOOPTIONS']._serialized_end = 2613
    _globals['_PLAYERQUEUE_ENTITYTYPE']._serialized_start = 2631
    _globals['_PLAYERQUEUE_ENTITYTYPE']._serialized_end = 2789
    _globals['_PLAYERQUEUE_ENTITYCONTEXT']._serialized_start = 2792
    _globals['_PLAYERQUEUE_ENTITYCONTEXT']._serialized_end = 2993
    _globals['_PLAYERSTATEOPTIONS']._serialized_start = 2996
    _globals['_PLAYERSTATEOPTIONS']._serialized_end = 3141
    _globals['_PLAYERSTATEOPTIONS_REPEATMODE']._serialized_start = 3084
    _globals['_PLAYERSTATEOPTIONS_REPEATMODE']._serialized_end = 3141
    _globals['_SHUFFLE']._serialized_start = 3143
    _globals['_SHUFFLE']._serialized_end = 3178
# @@protoc_insertion_point(module_scope)
