from datetime import datetime

import pytest

from nowplaying.core.config import config
from nowplaying.external.soundcloud import SoundCloudWrapper
from nowplaying.models.track import Track
from nowplaying.util.time import UTC_TZ


SC_TOKEN: str | None = config.TEST_ARGS.get('SOUNDCLOUD_TOKEN')


@pytest.fixture
async def sc_client() -> SoundCloudWrapper:
    assert SC_TOKEN
    return SoundCloudWrapper(SC_TOKEN)


@pytest.mark.asyncio
@pytest.mark.skipif(not SC_TOKEN, reason='no sc token')
async def test_sc_play_history(sc_client: SoundCloudWrapper) -> None:
    history = await sc_client.get_play_history()
    assert history


@pytest.mark.asyncio
@pytest.mark.skipif(not SC_TOKEN, reason='no sc token')
async def test_sc_get_track(sc_client: SoundCloudWrapper) -> None:
    track = await sc_client.get_track(1245462184)
    assert track

    assert track.id == 1245462184
    assert track.author == '...'
    assert track.title == 'everything i want for u ♦○♪'
    assert track.permalink_url == 'https://soundcloud.com/nkycat/everything-i-want-for-u'


@pytest.mark.asyncio
@pytest.mark.skipif(not SC_TOKEN, reason='no sc token')
async def test_sc_get_track_publisher_meta(sc_client: SoundCloudWrapper) -> None:
    track = await sc_client.get_track(1029241846)
    assert track

    assert track.id == 1029241846
    assert track.author == 'DJ Sharpnel'
    assert track.title == 'Pants'
    assert track.permalink_url == 'https://soundcloud.com/extasium/dj-sharpnel-pants'


@pytest.mark.asyncio
@pytest.mark.skipif(not SC_TOKEN, reason='no sc token')
async def test_sc_song_link_query(sc_client: SoundCloudWrapper) -> None:
    history = await sc_client.get_play_history()
    assert history

    track = await Track.from_soundcloud_item(
        track=history[0].track,
        currently_playing=False,
        played_at=datetime.fromtimestamp(0, tz=UTC_TZ),
    )
    song_link = await track.song_link()
    assert song_link
    assert song_link.startswith('https://song.link/sc/')
