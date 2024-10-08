from . import playable_pb2 as _playable_pb2
from . import update_version_pb2 as _update_version_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
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

class PlayerQueue(_message.Message):
    __slots__ = (
        'entity_id',
        'entity_type',
        'queue',
        'current_playable_index',
        'playable_list',
        'options',
        'version',
        'shuffle_optional',
        'entity_context',
        'from_optional',
        'initial_entity_optional',
        'adding_options_optional',
    )
    class EntityType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[PlayerQueue.EntityType]
        ARTIST: _ClassVar[PlayerQueue.EntityType]
        PLAYLIST: _ClassVar[PlayerQueue.EntityType]
        ALBUM: _ClassVar[PlayerQueue.EntityType]
        RADIO: _ClassVar[PlayerQueue.EntityType]
        VARIOUS: _ClassVar[PlayerQueue.EntityType]
        GENERATIVE: _ClassVar[PlayerQueue.EntityType]
        FM_RADIO: _ClassVar[PlayerQueue.EntityType]
        VIDEO_WAVE: _ClassVar[PlayerQueue.EntityType]
        LOCAL_TRACKS: _ClassVar[PlayerQueue.EntityType]

    UNSPECIFIED: PlayerQueue.EntityType
    ARTIST: PlayerQueue.EntityType
    PLAYLIST: PlayerQueue.EntityType
    ALBUM: PlayerQueue.EntityType
    RADIO: PlayerQueue.EntityType
    VARIOUS: PlayerQueue.EntityType
    GENERATIVE: PlayerQueue.EntityType
    FM_RADIO: PlayerQueue.EntityType
    VIDEO_WAVE: PlayerQueue.EntityType
    LOCAL_TRACKS: PlayerQueue.EntityType
    class EntityContext(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        BASED_ON_ENTITY_BY_DEFAULT: _ClassVar[PlayerQueue.EntityContext]
        USER_TRACKS: _ClassVar[PlayerQueue.EntityContext]
        DOWNLOADED_TRACKS: _ClassVar[PlayerQueue.EntityContext]
        SEARCH: _ClassVar[PlayerQueue.EntityContext]
        MUSIC_HISTORY: _ClassVar[PlayerQueue.EntityContext]
        MUSIC_HISTORY_SEARCH: _ClassVar[PlayerQueue.EntityContext]
        ARTIST_MY_COLLECTION: _ClassVar[PlayerQueue.EntityContext]
        ARTIST_FAMILIAR_FROM_WAVE: _ClassVar[PlayerQueue.EntityContext]

    BASED_ON_ENTITY_BY_DEFAULT: PlayerQueue.EntityContext
    USER_TRACKS: PlayerQueue.EntityContext
    DOWNLOADED_TRACKS: PlayerQueue.EntityContext
    SEARCH: PlayerQueue.EntityContext
    MUSIC_HISTORY: PlayerQueue.EntityContext
    MUSIC_HISTORY_SEARCH: PlayerQueue.EntityContext
    ARTIST_MY_COLLECTION: PlayerQueue.EntityContext
    ARTIST_FAMILIAR_FROM_WAVE: PlayerQueue.EntityContext
    class Queue(_message.Message):
        __slots__ = ('wave_queue', 'generative_queue', 'fm_radio_queue', 'video_wave_queue', 'local_tracks_queue')
        class WaveQueue(_message.Message):
            __slots__ = ('recommended_playable_list', 'live_playable_index', 'entity_options')
            class EntityOptions(_message.Message):
                __slots__ = ('wave_entity_optional', 'track_sources')
                class WaveSession(_message.Message):
                    __slots__ = ('session_id',)
                    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
                    session_id: str
                    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

                class TrackSourceWithKey(_message.Message):
                    __slots__ = ('key', 'wave_source', 'phonoteka_source')
                    KEY_FIELD_NUMBER: _ClassVar[int]
                    WAVE_SOURCE_FIELD_NUMBER: _ClassVar[int]
                    PHONOTEKA_SOURCE_FIELD_NUMBER: _ClassVar[int]
                    key: int
                    wave_source: PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSource
                    phonoteka_source: PlayerQueue.Queue.WaveQueue.EntityOptions.PhonotekaSource
                    def __init__(
                        self,
                        key: _Optional[int] = ...,
                        wave_source: _Optional[
                            _Union[PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSource, _Mapping]
                        ] = ...,
                        phonoteka_source: _Optional[
                            _Union[PlayerQueue.Queue.WaveQueue.EntityOptions.PhonotekaSource, _Mapping]
                        ] = ...,
                    ) -> None: ...

                class WaveSource(_message.Message):
                    __slots__ = ()
                    def __init__(self) -> None: ...

                class PhonotekaSource(_message.Message):
                    __slots__ = ('artist_id', 'playlist_id', 'album_id', 'entity_context')
                    ARTIST_ID_FIELD_NUMBER: _ClassVar[int]
                    PLAYLIST_ID_FIELD_NUMBER: _ClassVar[int]
                    ALBUM_ID_FIELD_NUMBER: _ClassVar[int]
                    ENTITY_CONTEXT_FIELD_NUMBER: _ClassVar[int]
                    artist_id: PlayerQueue.Queue.WaveQueue.EntityOptions.ArtistId
                    playlist_id: PlayerQueue.Queue.WaveQueue.EntityOptions.PlaylistId
                    album_id: PlayerQueue.Queue.WaveQueue.EntityOptions.AlbumId
                    entity_context: PlayerQueue.EntityContext
                    def __init__(
                        self,
                        artist_id: _Optional[
                            _Union[PlayerQueue.Queue.WaveQueue.EntityOptions.ArtistId, _Mapping]
                        ] = ...,
                        playlist_id: _Optional[
                            _Union[PlayerQueue.Queue.WaveQueue.EntityOptions.PlaylistId, _Mapping]
                        ] = ...,
                        album_id: _Optional[_Union[PlayerQueue.Queue.WaveQueue.EntityOptions.AlbumId, _Mapping]] = ...,
                        entity_context: _Optional[_Union[PlayerQueue.EntityContext, str]] = ...,
                    ) -> None: ...

                class ArtistId(_message.Message):
                    __slots__ = ('id',)
                    ID_FIELD_NUMBER: _ClassVar[int]
                    id: str
                    def __init__(self, id: _Optional[str] = ...) -> None: ...

                class PlaylistId(_message.Message):
                    __slots__ = ('id',)
                    ID_FIELD_NUMBER: _ClassVar[int]
                    id: str
                    def __init__(self, id: _Optional[str] = ...) -> None: ...

                class AlbumId(_message.Message):
                    __slots__ = ('id',)
                    ID_FIELD_NUMBER: _ClassVar[int]
                    id: str
                    def __init__(self, id: _Optional[str] = ...) -> None: ...

                WAVE_ENTITY_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
                TRACK_SOURCES_FIELD_NUMBER: _ClassVar[int]
                wave_entity_optional: PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSession
                track_sources: _containers.RepeatedCompositeFieldContainer[
                    PlayerQueue.Queue.WaveQueue.EntityOptions.TrackSourceWithKey
                ]
                def __init__(
                    self,
                    wave_entity_optional: _Optional[
                        _Union[PlayerQueue.Queue.WaveQueue.EntityOptions.WaveSession, _Mapping]
                    ] = ...,
                    track_sources: _Optional[
                        _Iterable[_Union[PlayerQueue.Queue.WaveQueue.EntityOptions.TrackSourceWithKey, _Mapping]]
                    ] = ...,
                ) -> None: ...

            RECOMMENDED_PLAYABLE_LIST_FIELD_NUMBER: _ClassVar[int]
            LIVE_PLAYABLE_INDEX_FIELD_NUMBER: _ClassVar[int]
            ENTITY_OPTIONS_FIELD_NUMBER: _ClassVar[int]
            recommended_playable_list: _containers.RepeatedCompositeFieldContainer[_playable_pb2.Playable]
            live_playable_index: int
            entity_options: PlayerQueue.Queue.WaveQueue.EntityOptions
            def __init__(
                self,
                recommended_playable_list: _Optional[_Iterable[_Union[_playable_pb2.Playable, _Mapping]]] = ...,
                live_playable_index: _Optional[int] = ...,
                entity_options: _Optional[_Union[PlayerQueue.Queue.WaveQueue.EntityOptions, _Mapping]] = ...,
            ) -> None: ...

        class GenerativeQueue(_message.Message):
            __slots__ = ('id',)
            ID_FIELD_NUMBER: _ClassVar[int]
            id: str
            def __init__(self, id: _Optional[str] = ...) -> None: ...

        class FmRadioQueue(_message.Message):
            __slots__ = ('id',)
            ID_FIELD_NUMBER: _ClassVar[int]
            id: str
            def __init__(self, id: _Optional[str] = ...) -> None: ...

        class VideoWaveQueue(_message.Message):
            __slots__ = ('id',)
            ID_FIELD_NUMBER: _ClassVar[int]
            id: str
            def __init__(self, id: _Optional[str] = ...) -> None: ...

        class LocalTracksQueue(_message.Message):
            __slots__ = ()
            def __init__(self) -> None: ...

        WAVE_QUEUE_FIELD_NUMBER: _ClassVar[int]
        GENERATIVE_QUEUE_FIELD_NUMBER: _ClassVar[int]
        FM_RADIO_QUEUE_FIELD_NUMBER: _ClassVar[int]
        VIDEO_WAVE_QUEUE_FIELD_NUMBER: _ClassVar[int]
        LOCAL_TRACKS_QUEUE_FIELD_NUMBER: _ClassVar[int]
        wave_queue: PlayerQueue.Queue.WaveQueue
        generative_queue: PlayerQueue.Queue.GenerativeQueue
        fm_radio_queue: PlayerQueue.Queue.FmRadioQueue
        video_wave_queue: PlayerQueue.Queue.VideoWaveQueue
        local_tracks_queue: PlayerQueue.Queue.LocalTracksQueue
        def __init__(
            self,
            wave_queue: _Optional[_Union[PlayerQueue.Queue.WaveQueue, _Mapping]] = ...,
            generative_queue: _Optional[_Union[PlayerQueue.Queue.GenerativeQueue, _Mapping]] = ...,
            fm_radio_queue: _Optional[_Union[PlayerQueue.Queue.FmRadioQueue, _Mapping]] = ...,
            video_wave_queue: _Optional[_Union[PlayerQueue.Queue.VideoWaveQueue, _Mapping]] = ...,
            local_tracks_queue: _Optional[_Union[PlayerQueue.Queue.LocalTracksQueue, _Mapping]] = ...,
        ) -> None: ...

    class InitialEntity(_message.Message):
        __slots__ = ('entity_id', 'entity_type')
        ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
        ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
        entity_id: str
        entity_type: PlayerQueue.EntityType
        def __init__(
            self, entity_id: _Optional[str] = ..., entity_type: _Optional[_Union[PlayerQueue.EntityType, str]] = ...
        ) -> None: ...

    class PlayerQueueOptions(_message.Message):
        __slots__ = ('radio_options',)
        class RadioOptions(_message.Message):
            __slots__ = ('session_id',)
            SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            session_id: str
            def __init__(self, session_id: _Optional[str] = ...) -> None: ...

        RADIO_OPTIONS_FIELD_NUMBER: _ClassVar[int]
        radio_options: PlayerQueue.PlayerQueueOptions.RadioOptions
        def __init__(
            self, radio_options: _Optional[_Union[PlayerQueue.PlayerQueueOptions.RadioOptions, _Mapping]] = ...
        ) -> None: ...

    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PLAYABLE_INDEX_FIELD_NUMBER: _ClassVar[int]
    PLAYABLE_LIST_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    SHUFFLE_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    ENTITY_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    FROM_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    INITIAL_ENTITY_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    ADDING_OPTIONS_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    entity_type: PlayerQueue.EntityType
    queue: PlayerQueue.Queue
    current_playable_index: int
    playable_list: _containers.RepeatedCompositeFieldContainer[_playable_pb2.Playable]
    options: PlayerStateOptions
    version: _update_version_pb2.UpdateVersion
    shuffle_optional: Shuffle
    entity_context: PlayerQueue.EntityContext
    from_optional: _wrappers_pb2.StringValue
    initial_entity_optional: PlayerQueue.InitialEntity
    adding_options_optional: PlayerQueue.PlayerQueueOptions
    def __init__(
        self,
        entity_id: _Optional[str] = ...,
        entity_type: _Optional[_Union[PlayerQueue.EntityType, str]] = ...,
        queue: _Optional[_Union[PlayerQueue.Queue, _Mapping]] = ...,
        current_playable_index: _Optional[int] = ...,
        playable_list: _Optional[_Iterable[_Union[_playable_pb2.Playable, _Mapping]]] = ...,
        options: _Optional[_Union[PlayerStateOptions, _Mapping]] = ...,
        version: _Optional[_Union[_update_version_pb2.UpdateVersion, _Mapping]] = ...,
        shuffle_optional: _Optional[_Union[Shuffle, _Mapping]] = ...,
        entity_context: _Optional[_Union[PlayerQueue.EntityContext, str]] = ...,
        from_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
        initial_entity_optional: _Optional[_Union[PlayerQueue.InitialEntity, _Mapping]] = ...,
        adding_options_optional: _Optional[_Union[PlayerQueue.PlayerQueueOptions, _Mapping]] = ...,
    ) -> None: ...

class PlayerStateOptions(_message.Message):
    __slots__ = ('repeat_mode',)
    class RepeatMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[PlayerStateOptions.RepeatMode]
        NONE: _ClassVar[PlayerStateOptions.RepeatMode]
        ONE: _ClassVar[PlayerStateOptions.RepeatMode]
        ALL: _ClassVar[PlayerStateOptions.RepeatMode]

    UNSPECIFIED: PlayerStateOptions.RepeatMode
    NONE: PlayerStateOptions.RepeatMode
    ONE: PlayerStateOptions.RepeatMode
    ALL: PlayerStateOptions.RepeatMode
    REPEAT_MODE_FIELD_NUMBER: _ClassVar[int]
    repeat_mode: PlayerStateOptions.RepeatMode
    def __init__(self, repeat_mode: _Optional[_Union[PlayerStateOptions.RepeatMode, str]] = ...) -> None: ...

class Shuffle(_message.Message):
    __slots__ = ('playable_indices',)
    PLAYABLE_INDICES_FIELD_NUMBER: _ClassVar[int]
    playable_indices: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, playable_indices: _Optional[_Iterable[int]] = ...) -> None: ...
