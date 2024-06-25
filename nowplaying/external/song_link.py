import re

import orjson
from aiohttp import ClientSession, ClientTimeout
from async_lru import alru_cache
from loguru import logger

from ..models.song_link import SongLinkInfo, SongLinkPlatform, SongLinkPlatformType
from ..util.http import STATUS_OK
from ..util.url import ParseResult, urlparse
from .song_link_parsers import fallback_to_odesli, get_song_link_parser


# For some reason httpx.AsyncClient sometimes just timeout shit for no reason, idek, tested on this url
# * https://song.link/ya/119843738
_client: ClientSession | None = None


async def _get_client() -> ClientSession:
    global _client  # noqa: WPS420

    if not _client:
        _client = ClientSession(  # noqa: WPS442, WPS122
            headers={
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Origin': 'https://odesli.co',
                'Pragma': 'no-cache',
                'Priority': 'u=1',
                'Referer': 'https://odesli.co',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Sec-GPC': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            },
            timeout=ClientTimeout(total=60.0),
        )

    return _client  # noqa: WPS121


@alru_cache()
async def get_song_link(track_url: str, allow_fallback: bool = True) -> str | None:
    url: ParseResult = urlparse(track_url)

    parser = get_song_link_parser(url.netloc)
    if parser:
        return parser(url)

    if not allow_fallback:
        return None

    return await fallback_to_odesli(await _get_client(), track_url)


def _parse_song_link_listen_section(
    song_link_info: SongLinkInfo,
    section: dict,
) -> None:
    for link in section.get('links', []):
        platform_name: str = link.get('platform', '')
        platform_url: str = link.get('url', '')
        if platform_name == '' or platform_url == '':
            continue

        try:
            platform_type = SongLinkPlatformType(platform_name)
        except ValueError:
            platform_type = SongLinkPlatformType.UNKNOWN
            logger.warning(f'Got an unknown platform: {platform_name}')

        song_link_info.platforms[platform_type] = SongLinkPlatform(
            platform=platform_type,
            url=platform_url,
        )


def _parse_song_link_page_data(
    sections: list[dict],
) -> SongLinkInfo:
    song_link_info = SongLinkInfo()

    for section in sections:
        display_name: str = section.get('displayName', '')

        song_link_info.thumbnail_url = section.get('thumbnailUrl', song_link_info.thumbnail_url)
        if display_name != 'Listen':
            continue

        _parse_song_link_listen_section(song_link_info, section)
        break

    return song_link_info


@alru_cache()
async def get_song_link_info(song_link_url: str) -> SongLinkInfo:
    resp = await (await _get_client()).get(song_link_url)
    if resp.status != STATUS_OK:  # this might be an issue in the future since we'll cache the empty set
        return SongLinkInfo()

    matched = re.search(
        r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(\{.*?})</script>',
        await resp.text(),
    )
    if not matched:
        return SongLinkInfo()

    try:
        next_data = orjson.loads(matched.group(1))
    except orjson.JSONDecodeError:
        return SongLinkInfo()

    props = next_data.get('props', {}).get('pageProps', {})
    sections = props.get('pageData', {}).get('sections', [])

    return _parse_song_link_page_data(sections)
