from pytest import mark

from nowplaying.external.deezer import search_tracks


@mark.asyncio
async def test_deezer_search() -> None:
    results = await search_tracks('MK - Crescent Moon')

    assert len(results) == 1
    assert results[0].id == '1265359402'
    assert results[0].title == 'Crescent Moon'
    assert results[0].album == 'Spirit Chords'
    assert results[0].album_id == '212492112'
    assert results[0].artist == 'MK (JPN)'
    assert results[0].artist_id == '10934636'
    assert results[0].url == 'https://www.deezer.com/track/1265359402'

