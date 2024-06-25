from datetime import datetime

from pydantic import BaseModel
from yandex_music import Track as YandexTrack

from ..external.apple import AppleMusicTrack
from ..external.lastfm import LastFMTrack
from ..external.song_link import get_song_link
from .song_link import SongLinkPlatformType


_TS_NULL = datetime.fromtimestamp(0)


class Track(BaseModel):
    platform: SongLinkPlatformType = SongLinkPlatformType.UNKNOWN

    artist: str = ''
    name: str = ''

    id: str | None
    url: str

    song_link: str | None

    currently_playing: bool = False
    played_at: datetime = _TS_NULL

    @property
    def full_title(self) -> str:
        return f'{self.artist} - {self.name}'

    @property
    def uri(self) -> str:
        platform_name: str = self.platform.value
        return f'{platform_name}_{self.id}'

    @property
    def is_available(self) -> bool:
        # todo: implement unavailable logic :sadge:
        return self.id is not None

    @classmethod
    async def from_spotify_item(
        cls,
        track_item: dict,
        played_at: datetime = _TS_NULL,
        is_playing: bool = False,
    ) -> 'Track':
        url: str = track_item['external_urls']['spotify']
        return cls(
            platform=SongLinkPlatformType.SPOTIFY,
            artist=', '.join([artist['name'] for artist in track_item['artists']]),
            name=track_item['name'],
            id=track_item['id'],
            url=url,
            song_link=await get_song_link(url),
            currently_playing=is_playing,
            played_at=played_at,
        )

    @classmethod
    async def from_lastfm_item(
        cls,
        track: LastFMTrack,
        *,
        track_id: str | None,
        song_link_url: str | None,
        played_at: datetime = _TS_NULL,
        is_playing: bool = False,
    ) -> 'Track':
        return cls(
            platform=SongLinkPlatformType.LASTFM,
            artist=track.artist,
            name=track.name,
            id=track_id,
            url=track.url,
            song_link=song_link_url,
            currently_playing=is_playing,
            played_at=played_at,
        )

    @classmethod
    async def from_yandex_item(
        cls,
        track: YandexTrack,
        played_at: datetime = _TS_NULL,
        is_playing: bool = False,
    ) -> 'Track':
        url = f'https://music.yandex.ru/track/{track.id}'
        return cls(
            platform=SongLinkPlatformType.YANDEX,
            artist=', '.join(track.artists_name()),
            name=track.title,
            id=track.id,
            url=url,
            song_link=await get_song_link(url),
            currently_playing=is_playing,
            played_at=played_at,
        )

    @classmethod
    async def from_apple_item(
        cls,
        track: AppleMusicTrack,
        currently_playing: bool = False,
        played_at: datetime = _TS_NULL,
    ) -> 'Track':
        return cls(
            platform=SongLinkPlatformType.APPLE,
            artist=track.artist,
            name=track.name,
            id=track.id,
            url=track.url,
            song_link=await get_song_link(track.url),
            currently_playing=currently_playing,
            played_at=played_at,
        )
