import re
from urllib.parse import parse_qs, urlparse

from aiohttp import ClientSession, ClientTimeout
from async_lru import alru_cache
from loguru import logger
from orjson import JSONDecodeError, loads

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
    url = urlparse(track_url)

    if track_url.startswith('https://open.spotify.com/track/'):
        # https://open.spotify.com/track/2ZAkKj4bPw2NM5bgLPOSVz
        track_id: str = url.path.split('/')[-1]
        return f'https://song.link/s/{track_id}'

    if 'music.yandex.' in url.netloc:  # .com or .ru
        # https://music.yandex.ru/track/79714180
        track_id = url.path.split('/')[-1]
        return f'https://song.link/ya/{track_id}'

    if url.netloc == 'music.apple.com':
        # https://music.apple.com/fr/album/imagine/1743455180?i=1743455190
        args = url.path.split('/')
        track_id = args[-1]
        if track_id.startswith('id'):
            track_id = track_id[2:]
        country: str = args[1]
        return f'https://song.link/{country}/i/{track_id}'

    if url.netloc == 'geo.music.apple.com':
        # https://geo.music.apple.com/album/id1606018075?i=1606018581&at=10l3Sh
        args = url.path.split('/')
        track_id = args[-1]
        if track_id.startswith('id'):
            track_id = track_id[2:]
        return f'https://song.link/i/{track_id}'

    if url.netloc.endswith('youtube.com'):
        # https://www.youtube.com/watch?v=TsfJfn4Ow2Q
        qs = parse_qs(url.query)
        v = qs.get('v', [''])
        return f'https://song.link/y/{v[0]}'

    logger.warning(f'Falling back to odesli api for the url: {track_url}')

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

    prefix = resp_json.get('provider', 'spotify')[0]
    return f'https://song.link/{prefix}/{resp_json["id"]}'


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


# async def tests() -> None:
#     assert (await get_song_link('https://www.youtube.com/watch?v=TsfJfn4Ow2Q&adhsjkasdhjk') ==
#             'https://song.link/y/TsfJfn4Ow2Q')
#     assert (await get_song_link('https://open.spotify.com/track/5L1eW2bt7pDbjhNLKWKom2?asdasdasd') ==
#             'https://song.link/s/5L1eW2bt7pDbjhNLKWKom2')
#     assert (await get_song_link('https://geo.music.apple.com/album/id1606018075?i=1606018581&at=10l3Sh') ==
#             'https://song.link/i/1606018075')
#     assert (await get_song_link('https://music.apple.com/fr/album/icarus/1606018075?i=1606018581') ==
#             'https://song.link/fr/i/1606018075')
#     assert (await get_song_link('https://music.yandex.ru/track/79714180') ==
#             'https://song.link/ya/79714180')
#     assert (await get_song_link('https://music.yandex.com/track/79714180') ==
#             'https://song.link/ya/79714180')
#
#     exit()
#
# from asyncio import run
#
# run(tests())
