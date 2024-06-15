from functools import lru_cache

from httpx import get
from orjson import loads


@lru_cache(maxsize=128)
def get_song_link(track_url: str | None) -> str | None:
    if not track_url:
        return None

    resp = get('https://api.odesli.co/resolve', params={
        'url': track_url,
    })
    if resp.status_code != 200:
        return None

    resp_json = loads(resp.text)
    if 'id' not in resp_json:
        return None

    return f'https://song.link/s/{resp_json["id"]}'
