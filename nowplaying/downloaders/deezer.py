from io import BytesIO

from nowplaying.bot.reporter import report_error
from nowplaying.external.deezer import (
    TYPE_TRACK,
    Deezer403Exception,
    Deezer404Exception,
    download_song,
    get_song_infos_from_deezer_website,
)
from nowplaying.models.song_link import SongLinkPlatform, SongLinkPlatformType
from nowplaying.util.logger import logger

from .abc import DownloaderABC


class DeezerDownloader(DownloaderABC):
    platform = SongLinkPlatformType.DEEZER

    async def download_mp3(self, platform: SongLinkPlatform) -> BytesIO | None:
        deezer_id = platform.url.split('/')[-1]
        logger.debug(f'Downloading {deezer_id}')

        try:
            song = await get_song_infos_from_deezer_website(TYPE_TRACK, deezer_id)
        except Deezer404Exception:
            return None
        except Deezer403Exception:
            await report_error('Deezer apl cookie is dead!! please update senpai')
            return None

        io = BytesIO()
        if not await download_song(song, io):
            return None

        io.seek(0)
        return io
