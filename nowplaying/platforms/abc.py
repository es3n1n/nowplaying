from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from types import MappingProxyType

from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track


# Will be thrown to signalize that something is wrong on the client side:
#   for example if a premium license of platform is needed to enqueue track.
#
# Can be thrown only within play and add_to_queue functions.
class PlatformClientSideError(Exception):
    pass


class PlatformClientABC(ABC):
    features: MappingProxyType[PlatformFeature, bool] = MappingProxyType(
        {
            PlatformFeature.TRACK_GETTERS: True,
            PlatformFeature.ADD_TO_QUEUE: False,
            PlatformFeature.PLAY: False,
        }
    )

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
    async def add_to_queue(self, track_id: str) -> None:
        """ """

    @abstractmethod
    async def play(self, track_id: str) -> None:
        """ """

    @property
    def can_control_playback(self) -> bool:
        can_control: bool = False
        for feature in (PlatformFeature.ADD_TO_QUEUE, PlatformFeature.PLAY):
            can_control = can_control or self.features.get(feature, False)
        return can_control


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
