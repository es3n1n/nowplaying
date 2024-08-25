from dataclasses import dataclass

import orjson
from httpx import AsyncClient

from nowplaying.util.http import get_headers


@dataclass
class DeezerTrack:
    id: str
    title: str

    album: str
    album_id: str

    artist: str
    artist_id: str

    @property
    def url(self) -> str:
        return f'https://www.deezer.com/track/{self.id}'


async def search_tracks(query: str) -> list[DeezerTrack]:
    # Note: For some reason, deezer returns a 403 error if query includes a `?` character
    query = query.replace('?', '')

    async with AsyncClient(headers=get_headers(legitimate_headers=True, chrome_user_agent=True)) as session:
        resp = await session.get(
            'https://api.deezer.com/search/track',
            params={
                'q': query,
            },
        )
        json_data = orjson.loads(resp.content)

    result = []
    for data in json_data.get('data', []):
        item_type = data.get('type', '')
        if item_type != 'track':
            continue

        result.append(
            DeezerTrack(
                id=str(data['id']),
                title=data['title'],
                album=data['album']['title'],
                album_id=str(data['album']['id']),
                artist=data['artist']['name'],
                artist_id=str(data['artist']['id']),
            )
        )

    return result
