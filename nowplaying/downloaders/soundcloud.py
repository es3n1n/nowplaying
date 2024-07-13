from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional

from requests import HTTPError
from scdl.scdl import SoundCloudException, download_hls, download_original_file, is_ffmpeg_available
from soundcloud import BasicTrack, SoundCloud, Track

from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.logger import logger
from .abc import DownloaderABC


if not is_ffmpeg_available():
    raise ValueError('Please install ffmpeg (and add it to the PATH if needed)')


class SoundcloudDownloader(DownloaderABC):
    platform = SongLinkPlatformType.SOUNDCLOUD

    def __init__(self):
        self.client = SoundCloud(client_id=None, auth_token=None)

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

        track = self.client.resolve(platform.url)
        if track is None or not isinstance(track, (BasicTrack, Track)):
            return None

        if not track.streamable or track.policy == 'BLOCK':
            return None

        kw = {
            'name_format': '-',
            'onlymp3': True,
            'title': '',
            'hide_progress': True,
            'c': True,
        }

        io = BytesIO()
        io.close = lambda: None  # type: ignore

        filename = None

        try:
            with redirect_stdout(io):  # type: ignore
                if track.downloadable:
                    filename, _ = download_original_file(self.client, track, **kw)

                if filename is None:
                    filename, _ = download_hls(self.client, track, **kw)
        except (SoundCloudException, HTTPError) as exc:
            logger.opt(exception=exc).warning('Got a soundcloud error while downloading')
            return None

        if filename is None:
            return None

        io.seek(0)
        return io
