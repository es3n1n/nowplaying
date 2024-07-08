from io import BytesIO

from pytest import mark

from nowplaying.downloaders import DOWNLOADERS
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.models.song_link import SongLinkPlatform


async def _download(platform_type: SongLinkPlatformType, song_url: str) -> BytesIO | None:
    downloader = DOWNLOADERS[platform_type]
    return await downloader.download_mp3(SongLinkPlatform(platform=platform_type, url=song_url))


@mark.asyncio
async def test_deezer() -> None:
    assert await _download(SongLinkPlatformType.DEEZER, 'https://www.deezer.com/track/1577218332') is not None


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