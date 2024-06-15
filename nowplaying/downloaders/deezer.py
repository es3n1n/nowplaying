from io import BytesIO
from typing import Optional

from ..bot.bot import bot
from ..core.config import config
from ..external.deezer import (
    TYPE_TRACK,
    Deezer403Exception,
    Deezer404Exception,
    download_song,
    get_song_infos_from_deezer_website,
)
from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.logger import logger
from .abc import DownloaderABC


class DeezerDownloader(DownloaderABC):
    platform = SongLinkPlatformType.DEEZER

    def __init__(self):
        pass

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        deezer_id = platform.url.split('/')[-1]
        logger.debug(f'Downloading {deezer_id}')

        try:
            song = await get_song_infos_from_deezer_website(TYPE_TRACK, deezer_id)
        except Deezer404Exception:
            return None
        except Deezer403Exception:
            await bot.send_message(config.BOT_DEV_CHAT_ID, 'Deezer apl cookie is dead!! please update senpai')
            return None

        io = BytesIO()
        if not await download_song(song, io):
            return None

        io.seek(0)
        return io
