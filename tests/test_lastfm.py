from pytest import mark

from nowplaying.external.lastfm import query_last_fm_url
from nowplaying.platforms.lastfm import query_song_link


@mark.asyncio
async def test_lfm_song_link_via_ext() -> None:
    link = await query_song_link(
        'https://www.last.fm/music/SAWTOWNE/_/M@GICAL+CURE!+LOVE+SHOT!+(feat.+Hatsune+Miku)'
    )

    assert link in (
        'https://song.link/i/1734570582',
        'https://song.link/y/LaEgpNBt-bQ',
        'https://song.link/s/63yoRZd5zl6Ah30hfDm97k',
    )


@mark.asyncio
async def test_lfm_song_link_via_deezer() -> None:
    link = await query_song_link('https://www.last.fm/music/MK/_/Crescent+Moon')

    assert link == 'https://song.link/d/1265359402'


@mark.asyncio
async def test_lfm_external_platforms_search() -> None:
    info = await query_last_fm_url(
        'https://www.last.fm/music/SAWTOWNE/_/M@GICAL+CURE!+LOVE+SHOT!+(feat.+Hatsune+Miku)',
    )

    assert info.track.artist == 'SAWTOWNE'
    assert info.track.name == 'M@GICAL CURE! LOVE SHOT! (feat. Hatsune Miku)'
    assert len(info.external_urls) == 3

    assert 'https://www.youtube.com/watch?v=LaEgpNBt-bQ' in info.external_urls
    assert 'https://open.spotify.com/track/63yoRZd5zl6Ah30hfDm97k' in info.external_urls
    assert 'https://geo.music.apple.com/album/id1734570580?i=1734570582&at=10l3Sh' in info.external_urls
