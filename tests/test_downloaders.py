from io import BytesIO

from pytest import mark, skip

from nowplaying.core.config import config
from nowplaying.downloaders import DOWNLOADERS
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.models.song_link import SongLinkPlatform


async def _download(platform_type: SongLinkPlatformType, song_url: str) -> BytesIO | None:
    downloader = DOWNLOADERS[platform_type]
    return await downloader.download_mp3(SongLinkPlatform(platform=platform_type, url=song_url))


@mark.asyncio
async def test_deezer() -> None:
    # Deezer cookie isn't set, skip the test
    if not config.deezer_apl_cookie_set:
        skip('Deezer cookie is not set')

    # Digital release date of this track is eq to None
    assert await _download(
        SongLinkPlatformType.DEEZER,
        'https://www.deezer.com/track/2931496091'
    ) is not None


@mark.asyncio
async def test_soundcloud() -> None:
    assert await _download(
        SongLinkPlatformType.SOUNDCLOUD,
        'https://soundcloud.com/vacationsfanclub/young-1',
    ) is not None


@mark.asyncio
async def test_youtube() -> None:
    assert await _download(
        SongLinkPlatformType.YOUTUBE,
        'https://www.youtube.com/watch?v=bp3991bNGO4',
    ) is not None


@mark.asyncio
@mark.skip(reason='Yt-dlp is having a bad time right now and cobalt doesnt always let you download this video')
async def test_youtube_18plus() -> None:
    assert await _download(
        SongLinkPlatformType.YOUTUBE,
        'https://www.youtube.com/watch?v=R1M2Wnc5LYc',
    ) is not None
