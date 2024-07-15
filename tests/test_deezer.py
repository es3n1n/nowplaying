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


@mark.asyncio
async def test_deezer_search_jp_title() -> None:
    results_jp = await search_tracks('Homecomings - ラプス')
    results_en = await search_tracks('Homecomings - Lapse')

    assert results_en == results_jp
    assert results_jp[0].title == 'Lapse'
    assert results_jp[0].artist == 'Homecomings'


@mark.asyncio
async def test_deezer_search_jp_artist() -> None:
    results_jp = await search_tracks('kessoku band - あのバンド - That band')
    results_en = await search_tracks('結束バンド - あのバンド')

    assert results_en[0] == results_jp[0]
    assert results_jp[0].title == 'That band'
    assert results_jp[0].artist == 'kessoku band'
