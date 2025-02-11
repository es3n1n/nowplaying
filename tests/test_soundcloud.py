import pytest

from nowplaying.core.config import config
from nowplaying.external.soundcloud import SoundCloudWrapper


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
    assert track.author_username == '...'
    assert track.title == 'everything i want for u ♦○♪'
    assert track.permalink_url == 'https://soundcloud.com/nkycat/everything-i-want-for-u'
