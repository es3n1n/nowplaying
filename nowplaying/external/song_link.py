from aiohttp import ClientSession, ClientTimeout
from async_lru import alru_cache

from nowplaying.util.http import get_headers
from nowplaying.util.url import ParseResult, urlparse

from .song_link_parsers import SOUND_CLOUD_URI, fallback_to_odesli, get_sc_from_uri_link, get_song_link_parser


@alru_cache()
async def get_song_link(track_url: str, *, allow_fallback: bool = True) -> str | None:
    # Special treatment for the soundcloud uris
    if track_url.startswith(SOUND_CLOUD_URI):
        return get_sc_from_uri_link(track_url)

    url: ParseResult = urlparse(track_url)
    parser = get_song_link_parser(url.netloc)
    if parser:
        return parser(url)

    if not allow_fallback:
        return None

    async with ClientSession(
        headers=get_headers(
            legitimate_headers=True,
            chrome_user_agent=True,
            origin='https://odesli.co',
            referer='https://odesli.co',
        ),
        timeout=ClientTimeout(total=60.0),
    ) as client:
        return await fallback_to_odesli(client, track_url)
