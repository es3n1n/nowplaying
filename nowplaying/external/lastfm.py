from re import DOTALL, compile, findall, search

from async_lru import alru_cache
from httpx import AsyncClient


client = AsyncClient(headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0'
}, follow_redirects=True)

PLAY_LINKS_REGEX = compile(r'<ul\sclass="play-this-track-playlinks">(.*?)</ul>', DOTALL)
HREF_URL_REGEX = compile(r'href="(https://.{1,100})"')


@alru_cache(maxsize=32)
async def query_lastfm_external_track_links(track: str) -> list[str]:
    response = await client.get(track)
    if response.status_code != 200:
        raise ValueError(f'Got status code {response.status_code}')

    container = search(PLAY_LINKS_REGEX, response.text)
    if container is None:
        return []

    result = list(set(findall(HREF_URL_REGEX, container.group(1))))
    return result
