from io import BytesIO
from os import remove
from pathlib import Path
from typing import Optional

from scdl import scdl as sc_dl
from scdl.scdl import download_hls, download_original_file
from soundcloud import BasicTrack, SoundCloud, Track

from ..models.song_link import SongLinkPlatform, SongLinkPlatformType
from ..util.fs import temp_file
from ..util.logger import logger
from .abc import DownloaderABC


def get_filename(track: BasicTrack, original_filename=None, aac=False, playlist_info=None, **kwargs):
    ext = '.m4a' if aac else '.mp3'  # contain aac in m4a to write metadata
    path: Path = kwargs['name_format']
    return path.parent / (path.name + ext)


sc_dl.get_filename = get_filename


class SoundcloudDownloader(DownloaderABC):
    platform = SongLinkPlatformType.SOUNDCLOUD

    def __init__(self):
        self.client = SoundCloud(client_id=None, auth_token=None)

    async def download_mp3(self, platform: SongLinkPlatform) -> Optional[BytesIO]:
        logger.debug(f'Downloading {platform.url}')

        track = self.client.resolve(platform.url)
        if track is None:
            return None

        if track.kind != 'track' or not isinstance(track, (BasicTrack, Track)):
            return None

        if not track.streamable or track.policy == 'BLOCK':
            return None

        filename = None
        is_already_downloaded = False

        kw = {
            'name_format': temp_file(),
            'onlymp3': True,
            'title': '',
        }

        if track.downloadable:
            filename, is_already_downloaded = download_original_file(self.client, track, **kw)

        if filename is None:
            filename, is_already_downloaded = download_hls(self.client, track, **kw)

        if filename is None:
            return None

        # fixme: @es3n1n: not sure how to fix this epic overhead since ffmpeg encodes stuff to files :thinking:
        io = BytesIO()
        with open(filename, 'rb') as out_file:
            io.write(out_file.read())

        io.seek(0)
        remove(filename)
        return io
