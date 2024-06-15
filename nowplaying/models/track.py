from pydantic import BaseModel

from ..core.song_link import get_song_link


class Track(BaseModel):
    artist: str
    name: str
    uri: str
    id: str
    url: str
    song_link: str | None
    currently_playing: bool = False

    @classmethod
    async def from_spotify_item(cls, track_item: dict, is_playing: bool = False) -> 'Track':
        url: str = track_item['external_urls']['spotify']
        return cls(
            artist=', '.join([x['name'] for x in track_item['artists']]),
            name=track_item['name'],
            uri=track_item['uri'],
            id=track_item['id'],
            url=url,
            song_link=await get_song_link(url),
            currently_playing=is_playing,
        )
