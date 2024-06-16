from datetime import datetime

from pydantic import BaseModel
from pylast import Track as LFMTrack
from yandex_music import Track as YandexTrack

from ..external.song_link import get_song_link
from .song_link import SongLinkPlatformType


_TS_NULL = datetime.fromtimestamp(0)


class Track(BaseModel):
    platform: SongLinkPlatformType = SongLinkPlatformType.UNKNOWN

    artist: str
    name: str

    id: str
    url: str

    song_link: str | None

    currently_playing: bool = False
    played_at: datetime = _TS_NULL

    @property
    def full_title(self) -> str:
        return f'{self.artist} - {self.name}'

    @property
    def uri(self) -> str:
        return f'{self.platform.value}_{self.id}'

    @classmethod
    async def from_spotify_item(
            cls,
            track_item: dict,
            played_at: datetime = _TS_NULL,
            is_playing: bool = False
    ) -> 'Track':
        url: str = track_item['external_urls']['spotify']
        return cls(
            platform=SongLinkPlatformType.SPOTIFY,
            artist=', '.join([x['name'] for x in track_item['artists']]),
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
            track: LFMTrack,
            played_at: datetime = _TS_NULL,
            is_playing: bool = False
    ) -> 'Track':
        url = track.get_url()
        return cls(
            platform=SongLinkPlatformType.LASTFM,
            artist=track.artist.name,
            name=track.title,
            id=f'{track.artist.name}_{track.title}',
            url=url,
            song_link=await get_song_link(url),
            currently_playing=is_playing,
            played_at=played_at,
        )

    @classmethod
    async def from_yandex_item(
            cls,
            track: YandexTrack,
            played_at: datetime = _TS_NULL,
            is_playing: bool = False
    ) -> 'Track':
        url = f'https://music.yandex.ru/track/{track.id}'
        return cls(
            platform=SongLinkPlatformType.LASTFM,
            artist=', '.join(track.artists_name()),
            name=track.title,
            id=track.id,
            url=url,
            song_link=await get_song_link(url),
            currently_playing=is_playing,
            played_at=played_at,
        )
