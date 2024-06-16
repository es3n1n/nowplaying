from abc import ABC, abstractmethod
from typing import AsyncIterator

from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track


class PlatformClientABC(ABC):
    features = {
        'track_getters': True,
        'add_to_queue': False,
        'play': False
    }

    @abstractmethod
    async def get_current_playing_track(self) -> Track | None:
        """ """

    @abstractmethod
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        yield Track(artist='', name='', id='', url='', song_link=None)

    @abstractmethod
    async def get_track(self, track_id: str) -> Track | None:
        """ """

    @abstractmethod
    async def add_to_queue(self, track_id: str) -> bool:
        """ """

    @abstractmethod
    async def play(self, track_id: str) -> bool:
        """ """

    @property
    def can_control_playback(self) -> bool:
        return self.features.get('add_to_queue', False) or self.features.get('play', False)


class PlatformABC(ABC):
    type: SongLinkPlatformType = SongLinkPlatformType.UNKNOWN

    @abstractmethod
    async def from_auth_callback(self, telegram_id: int, auth_code: str) -> PlatformClientABC:
        """ """

    @abstractmethod
    async def from_telegram_id(self, telegram_id: int) -> PlatformClientABC:
        """ """

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """ """
