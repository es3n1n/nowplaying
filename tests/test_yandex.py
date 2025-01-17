import pytest

from nowplaying.core.config import config
from nowplaying.external.yandex import ClientAsync
from nowplaying.platforms.yandex import YandexClient


YM_TOKEN: str | None = config.TEST_ARGS.get('YANDEX_TOKEN')


@pytest.fixture
def ym_client() -> YandexClient:
    assert YM_TOKEN
    return YandexClient(ClientAsync(YM_TOKEN), 1337)


@pytest.mark.skipif(not YM_TOKEN, reason='no yandex token')
async def test_getter(ym_client: YandexClient) -> None:
    track = await ym_client.get_track('48723231')
    assert track
    assert track.artist == 'Lil Skies'
    assert track.name == 'Real Ties'
