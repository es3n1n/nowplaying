from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Playable(_message.Message):
    __slots__ = (
        'playable_id',
        'album_id_optional',
        'playable_type',
        'title',
        'cover_url_optional',
        'video_clip_info',
        'track_info',
    )
    class PlayableType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[Playable.PlayableType]
        TRACK: _ClassVar[Playable.PlayableType]
        LOCAL_TRACK: _ClassVar[Playable.PlayableType]
        INFINITE: _ClassVar[Playable.PlayableType]
        VIDEO_CLIP: _ClassVar[Playable.PlayableType]

    UNSPECIFIED: Playable.PlayableType
    TRACK: Playable.PlayableType
    LOCAL_TRACK: Playable.PlayableType
    INFINITE: Playable.PlayableType
    VIDEO_CLIP: Playable.PlayableType
    PLAYABLE_ID_FIELD_NUMBER: _ClassVar[int]
    ALBUM_ID_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    PLAYABLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FROM_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    COVER_URL_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    VIDEO_CLIP_INFO_FIELD_NUMBER: _ClassVar[int]
    TRACK_INFO_FIELD_NUMBER: _ClassVar[int]
    playable_id: str
    album_id_optional: _wrappers_pb2.StringValue
    playable_type: Playable.PlayableType
    title: str
    cover_url_optional: _wrappers_pb2.StringValue
    video_clip_info: VideoClipInfo
    track_info: TrackInfo
    def __init__(
        self,
        playable_id: _Optional[str] = ...,
        album_id_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
        playable_type: _Optional[_Union[Playable.PlayableType, str]] = ...,
        title: _Optional[str] = ...,
        cover_url_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
        video_clip_info: _Optional[_Union[VideoClipInfo, _Mapping]] = ...,
        track_info: _Optional[_Union[TrackInfo, _Mapping]] = ...,
        **kwargs,
    ) -> None: ...

class VideoClipInfo(_message.Message):
    __slots__ = ('recommendation_type',)
    class RecommendationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[VideoClipInfo.RecommendationType]
        RECOMMENDED: _ClassVar[VideoClipInfo.RecommendationType]
        ON_DEMAND: _ClassVar[VideoClipInfo.RecommendationType]

    UNSPECIFIED: VideoClipInfo.RecommendationType
    RECOMMENDED: VideoClipInfo.RecommendationType
    ON_DEMAND: VideoClipInfo.RecommendationType
    RECOMMENDATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    recommendation_type: VideoClipInfo.RecommendationType
    def __init__(self, recommendation_type: _Optional[_Union[VideoClipInfo.RecommendationType, str]] = ...) -> None: ...

class TrackInfo(_message.Message):
    __slots__ = ('track_source_key', 'batch_id_optional')
    TRACK_SOURCE_KEY_FIELD_NUMBER: _ClassVar[int]
    BATCH_ID_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    track_source_key: int
    batch_id_optional: _wrappers_pb2.StringValue
    def __init__(
        self,
        track_source_key: _Optional[int] = ...,
        batch_id_optional: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ...,
    ) -> None: ...
