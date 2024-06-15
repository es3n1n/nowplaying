import re

from async_lru import alru_cache
from httpx import AsyncClient, Timeout
from loguru import logger
from orjson import JSONDecodeError, loads

from ..models.song_link import SongLinkInfo, SongLinkPlatform, SongLinkPlatformType


client = AsyncClient(headers={
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
}, timeout=Timeout(timeout=60.))


async def get_song_link(track_url: str) -> str:
    uri: str = track_url.split('/')[-1]
    return f'https://song.link/s/{uri}'


@alru_cache(maxsize=128)
async def get_song_link_info(song_link_url: str) -> SongLinkInfo:
    result = SongLinkInfo(
        platforms=dict(),
        thumbnail_url=''
    )

    resp = await client.get(song_link_url)
    if resp.status_code != 200:  # this might be an issue in the future since we'll cache the empty set
        return result

    matched = re.search(
        r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(\{.*?})</script>',
        resp.text,
    )
    if not matched:
        return result

    try:
        next_data = loads(matched.group(1))
    except JSONDecodeError:
        return result

    page_data = next_data.get('props', {}).get('pageProps', {}).get('pageData', {})
    sections = page_data.get('sections', [])

    for section in sections:
        display_name: str = section.get('displayName', '')

        if 'thumbnailUrl' in section:
            result.thumbnail_url = section['thumbnailUrl']

        if display_name != 'Listen':
            continue

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

            result.platforms[platform_type] = SongLinkPlatform(
                platform=platform_type,
                url=platform_url,
            )
        break

    return result
