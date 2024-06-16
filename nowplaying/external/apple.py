from async_lru import alru_cache
from httpx import AsyncClient
from orjson import JSONDecodeError, loads

from nowplaying.util.logger import logger


client = AsyncClient(headers={
    'Pragma': 'no-cache',
    'Origin': 'https://odesli.co',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 '
                  'Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Cache-Control': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Referer': 'https://odesli.co/',
    'DNT': '1',
})


@alru_cache(maxsize=128)
async def find_song_in_apple_music(artist: str, name: str, country: str = 'US') -> int | None:
    resp = await client.get('https://itunes.apple.com/search', params={
        'term': f'{artist} - {name}',
        'country': country,
        'entity': 'song',
    })

    try:
        resp_json = loads(resp.text)
    except JSONDecodeError:
        return None

    if 'results' not in resp_json:
        logger.warning(f'Got suspicious response from itunes: {resp_json}')
        return None

    results = resp_json['results']
    if len(results) == 0:
        return None

    return results[0]['trackId']
