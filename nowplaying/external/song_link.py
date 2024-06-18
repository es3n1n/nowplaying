import re
from urllib.parse import unquote

from aiohttp import ClientSession, ClientTimeout
from async_lru import alru_cache
from loguru import logger
from orjson import JSONDecodeError, loads

from ..external.apple import find_song_in_apple_music
from ..models.song_link import SongLinkInfo, SongLinkPlatform, SongLinkPlatformType


# For some reason httpx.AsyncClient sometimes just timeout shit for no reason, idek, tested on this url
# * https://song.link/ya/119843738
_client: ClientSession | None = None


async def _get_client() -> ClientSession:
    global _client

    if not _client:
        _client = ClientSession(
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
            },
            timeout=ClientTimeout(total=60.)
        )

    return _client


@alru_cache(maxsize=128)
async def get_song_link(track_url: str) -> str | None:
    if track_url.startswith('https://open.spotify.com/track/'):
        uri: str = track_url.split('/')[-1]
        return f'https://song.link/s/{uri}'

    if track_url.startswith('https://www.last.fm/music/'):
        args = track_url.split('/')
        track_name = unquote(unquote(args[-1])).replace('+', ' ')
        artist_name = unquote(unquote(args[-3])).replace('+', ' ')

        itunes_id = await find_song_in_apple_music(artist_name, track_name)
        if itunes_id is None:
            return None

        return f'https://song.link/us/i/{itunes_id}'

    if track_url.startswith('https://music.yandex.'):  # .com or .ru
        track_id: str = track_url.split('/')[-1]
        return f'https://song.link/ya/{track_id}'

    if track_url.startswith('https://music.apple.com/'):
        # https://music.apple.com/fr/album/imagine/1743455180?i=1743455190
        args = track_url.split('?')[0].split('/')
        track_id = args[-1]
        country: str = args[3]
        return f'https://song.link/{country}/i/{track_id}'

    cl = await _get_client()
    resp = await cl.get('https://api.odesli.co/resolve', params={
        'url': track_url,
    })
    if resp.status != 200:
        return None

    try:
        resp_json = loads(await resp.text())
    except JSONDecodeError:
        return None

    if 'id' not in resp_json:
        return None

    return f'https://song.link/s/{resp_json["id"]}'


@alru_cache(maxsize=128)
async def get_song_link_info(song_link_url: str) -> SongLinkInfo:
    result = SongLinkInfo(
        platforms=dict(),
        thumbnail_url=''
    )

    cl = await _get_client()
    resp = await cl.get(song_link_url)
    if resp.status != 200:  # this might be an issue in the future since we'll cache the empty set
        return result

    matched = re.search(
        r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(\{.*?})</script>',
        await resp.text(),
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
