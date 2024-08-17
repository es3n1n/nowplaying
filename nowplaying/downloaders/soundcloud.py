from contextlib import redirect_stdout
from io import BytesIO
from shutil import which

from requests import HTTPError
from scdl.scdl import SoundCloudException, download_hls, download_original_file
from soundcloud import BasicTrack, SoundCloud, Track

from nowplaying.models.song_link import SongLinkPlatform, SongLinkPlatformType
from nowplaying.util.logger import logger

from .abc import DownloaderABC


if which('ffmpeg') is None:
    msg = 'Please install ffmpeg (and add it to the PATH if needed)'
    raise ValueError(msg)


class SoundcloudDownloader(DownloaderABC):
    platform = SongLinkPlatformType.SOUNDCLOUD

    def __init__(self) -> None:
        self.client = SoundCloud(client_id=None, auth_token=None)

    async def download_mp3(self, platform: SongLinkPlatform) -> BytesIO | None:
        logger.debug(f'Downloading {platform.url}')

        track = self.client.resolve(platform.url)
        if track is None or not isinstance(track, BasicTrack | Track):
            return None

        if not track.streamable or track.policy == 'BLOCK':
            return None

        kw = {
            'name_format': '-',
            'onlymp3': True,
            'hide_progress': True,
            'c': True,
            'debug': False,
        }

        io = BytesIO()
        filename = None

        try:
            with redirect_stdout(io):  # type: ignore[type-var]
                if track.downloadable:
                    filename, _ = download_original_file(self.client, track, title='', kwargs=kw)

                if filename is None:
                    filename, _ = download_hls(self.client, track, title='', kwargs=kw)
        except (SoundCloudException, HTTPError) as exc:
            logger.opt(exception=exc).warning('Got a soundcloud error while downloading')
            return None

        if filename is None:
            return None

        io.seek(0)
        return io
