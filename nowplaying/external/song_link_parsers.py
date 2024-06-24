from types import MappingProxyType
from typing import Callable
from urllib.parse import ParseResult, parse_qs

import orjson
from aiohttp import ClientSession

from ..util.http import STATUS_OK
from ..util.logger import logger


def get_spotify_link(url: ParseResult) -> str:
    track_id = url.path.split('/')[-1]
    return f'https://song.link/s/{track_id}'


def get_yandex_link(url) -> str:
    track_id = url.path.split('/')[-1]
    return f'https://song.link/ya/{track_id}'


def get_apple_link(url) -> str:
    path_parts = url.path.split('/')
    country = path_parts[1]
    album_id = path_parts[-1]
    if album_id.startswith('id'):
        album_id = album_id[2:]

    qs = parse_qs(url.query)
    track_id: str | None = qs.get('i', [None])[0]
    if track_id is not None:
        return f'https://song.link/i/{track_id}'

    return f'https://album.link/{country}/i/{album_id}'


def get_geo_apple_link(url) -> str:
    track_id = url.path.split('/')[-1]
    if track_id.startswith('id'):
        track_id = track_id[2:]
    return f'https://song.link/i/{track_id}'


def get_youtube_link(url) -> str:
    qs = parse_qs(url.query)
    video_id = qs.get('v', [''])[0]
    return f'https://song.link/y/{video_id}'


async def fallback_to_odesli(client: ClientSession, track_url: str):
    logger.warning(f'Falling back to Odesli API for the URL: {track_url}')
    response = await client.get('https://api.odesli.co/resolve', params={'url': track_url})

    if response.status != STATUS_OK:
        return None

    try:
        response_json = orjson.loads(await response.text())
    except orjson.JSONDecodeError:
        return None

    if 'id' not in response_json:
        return None

    provider_prefix = response_json.get('provider', 'spotify')[0]
    return f'https://song.link/{provider_prefix}/{response_json["id"]}'


SONG_LINK_PARSERS: MappingProxyType[str, Callable[[ParseResult], str]] = MappingProxyType({
    'open.spotify.com': get_spotify_link,
    'music.yandex.ru': get_yandex_link,
    'music.yandex.com': get_yandex_link,
    'music.apple.com': get_apple_link,
    'geo.music.apple.com': get_geo_apple_link,
    'youtube.com': get_youtube_link,
})
