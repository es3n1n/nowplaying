from types import MappingProxyType
from typing import Callable
from urllib.parse import ParseResult, parse_qs

import orjson
from aiohttp import ClientSession

from ..bot.reporter import report_error
from ..enums.resolved_platform_type import ResolvedPlatformType
from ..util.http import STATUS_OK


# source: https://odesli.co/_next/static/chunks/pages/index-5b40c5e4b10da55d.js
ODESLI_SHORT_NAMES: MappingProxyType[ResolvedPlatformType, str] = MappingProxyType({
    ResolvedPlatformType.AMAZON_MUSIC: 'a',
    ResolvedPlatformType.AUDIOMACK: 'am',
    ResolvedPlatformType.AUDIUS: 'au',
    ResolvedPlatformType.BANDCAMP: 'b',
    ResolvedPlatformType.BOOM_PLAY: 'bp',
    ResolvedPlatformType.DEEZER: 'd',
    ResolvedPlatformType.ITUNES: 'i',
    ResolvedPlatformType.NAPSTER: 'n',
    ResolvedPlatformType.PANDORA: 'p',
    ResolvedPlatformType.SOUNDCLOUD: 'sc',
    ResolvedPlatformType.SPINRILLA: 'sp',
    ResolvedPlatformType.SPOTIFY: 's',
    ResolvedPlatformType.TIDAL: 't',
    ResolvedPlatformType.YANDEX: 'ya',
    ResolvedPlatformType.YOUTUBE: 'y',
})


def get_stub_from_path(platform: ResolvedPlatformType) -> Callable[[ParseResult], str]:
    platform_short_name: str | None = ODESLI_SHORT_NAMES.get(platform, None)

    if platform_short_name is None:
        raise ValueError(f'{platform} is unsupported')

    def wrapper(url: ParseResult) -> str:
        track_id: str = url.path.split('/')[-1]
        return f'https://song.link/{platform_short_name}/{track_id}'

    return wrapper


def get_apple_link(url: ParseResult) -> str:
    path_parts = url.path.split('/')
    album_id = path_parts[-1]
    if album_id.startswith('id'):
        album_id = album_id[2:]

    # todo: should we include the country(`path_parts[1]`) here too?
    #  not sure as
    #  both https://album.link/i/1606018075 and https://album.link/fr/i/1606018075 works
    #  also https://song.link/i/1606018581 and https://song.link/fr/i/1606018581 works just fine too
    #  if we really decide to do this, then please note that geo apple music links doesn't include the region

    qs = parse_qs(url.query)
    track_id: str | None = qs.get('i', [None])[0]
    if track_id is not None:
        return f'https://song.link/i/{track_id}'

    return f'https://album.link/i/{album_id}'


def get_youtube_link(url: ParseResult) -> str:
    qs = parse_qs(url.query)
    video_id = qs.get('v', [''])[0]
    return f'https://song.link/y/{video_id}'


async def fallback_to_odesli(client: ClientSession, track_url: str, ignore_reporting: bool = False):
    if not ignore_reporting:
        await report_error(f'Falling back to Odesli API for the URL: {track_url}')
    response = await client.get('https://api.odesli.co/resolve', params={'url': track_url})

    if response.status != STATUS_OK:
        return None

    try:
        response_json = orjson.loads(await response.text())
    except orjson.JSONDecodeError:
        return None

    if 'id' not in response_json:
        return None

    provider = ResolvedPlatformType(response_json.get('provider', 'spotify'))
    prefix: str | None = ODESLI_SHORT_NAMES.get(provider, None)

    if prefix is None:
        raise ValueError(f'provider {response_json.get("provider")} is unsupported. Body: {response_json}')

    return f'https://song.link/{prefix}/{response_json["id"]}'


def get_song_link_parser(domain: str) -> Callable[[ParseResult], str] | None:
    # Special silly handling for the yandex music as they have lots of domains
    if domain.startswith('music.yandex.'):
        return SONG_LINK_PARSERS.get('music.yandex.com')
    return SONG_LINK_PARSERS.get(domain)


SONG_LINK_PARSERS: MappingProxyType[str, Callable[[ParseResult], str]] = MappingProxyType({
    'open.spotify.com': get_stub_from_path(ResolvedPlatformType.SPOTIFY),
    'play.spotify.com': get_stub_from_path(ResolvedPlatformType.SPOTIFY),

    'music.yandex.com': get_stub_from_path(ResolvedPlatformType.YANDEX),

    'itunes.apple.com': get_apple_link,
    'music.apple.com': get_apple_link,
    'geo.music.apple.com': get_apple_link,

    'youtube.com': get_youtube_link,
    'youtu.be': get_stub_from_path(ResolvedPlatformType.YOUTUBE),

    'deezer.com': get_stub_from_path(ResolvedPlatformType.DEEZER),
})
