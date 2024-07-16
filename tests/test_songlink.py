from pytest import mark

from nowplaying.external.song_link import _get_client, get_song_link
from nowplaying.external.song_link_parsers import fallback_to_odesli


async def get(link: str) -> str | None:
    return await get_song_link(link, allow_fallback=False)


@mark.asyncio
async def test_youtube() -> None:
    assert (
        await get('https://www.youtube.com/watch?v=TsfJfn4Ow2Q') ==
        'https://song.link/y/TsfJfn4Ow2Q'
    )
    assert (
        await get('https://youtu.be/TsfJfn4Ow2Q') ==
        'https://song.link/y/TsfJfn4Ow2Q'
    )
    assert (
        await get('https://www.youtube.com/watch?v=TsfJfn4Ow2Q&adhsjkasdhjk') ==
        'https://song.link/y/TsfJfn4Ow2Q'
    )


@mark.asyncio
async def test_spotify() -> None:
    assert (
        await get('https://open.spotify.com/track/5L1eW2bt7pDbjhNLKWKom2') ==
        'https://song.link/s/5L1eW2bt7pDbjhNLKWKom2'
    )
    assert (
        await get('https://play.spotify.com/track/5L1eW2bt7pDbjhNLKWKom2') ==
        'https://song.link/s/5L1eW2bt7pDbjhNLKWKom2'
    )
    assert (
        await get('https://open.spotify.com/track/5L1eW2bt7pDbjhNLKWKom2?asdasdasd') ==
        'https://song.link/s/5L1eW2bt7pDbjhNLKWKom2'
    )


@mark.asyncio
async def test_apple_music() -> None:
    assert (
        await get('https://geo.music.apple.com/album/id1606018075?i=1606018581&at=10l3Sh') ==
        'https://song.link/i/1606018581'
    )
    assert (
        await get('https://itunes.apple.com/fr/album/icarus/1606018075?i=1606018581') ==
        'https://song.link/i/1606018581'
    )
    assert (
        await get('https://music.apple.com/fr/album/icarus/1606018075?i=1606018581') ==
        'https://song.link/i/1606018581'
    )
    assert (
        await get('https://music.apple.com/fr/album/icarus/1606018075') ==
        'https://album.link/i/1606018075'
    )


@mark.asyncio
async def test_yandex_music() -> None:
    assert (
        await get_song_link('https://music.yandex.ru/track/79714180') ==
        'https://song.link/ya/79714180'
    )
    assert (
        await get_song_link('https://music.yandex.com/track/79714180') ==
        'https://song.link/ya/79714180'
    )
    assert (
        await get_song_link('https://music.yandex.ie/track/79714180') ==
        'https://song.link/ya/79714180'
    )


@mark.asyncio
async def test_fallback() -> None:
    assert (
        await fallback_to_odesli(
            await _get_client(),
            'https://music.yandex.ru/track/79714180',
            True
        ) == 'https://song.link/ya/79714180'
    )
