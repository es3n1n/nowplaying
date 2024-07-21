from abc import ABC, abstractmethod
from functools import wraps
from inspect import isasyncgenfunction
from typing import AsyncIterator, Callable

from ..core.database import db
from ..enums.platform_features import PlatformFeature
from ..models.song_link import SongLinkPlatformType
from ..models.track import Track


class PlatformClientABC(ABC):
    features: dict[PlatformFeature, bool] = {
        PlatformFeature.TRACK_GETTERS: True,
        PlatformFeature.ADD_TO_QUEUE: False,
        PlatformFeature.PLAY: False,
    }

    @abstractmethod
    async def get_current_playing_track(self) -> Track | None:
        """ """

    @abstractmethod
    async def get_current_and_recent_tracks(self, limit: int) -> AsyncIterator[Track]:
        yield Track(artist='', name='', id='', url='', song_link=None)

    @abstractmethod
    async def add_to_queue(self, track_id: str) -> bool:
        """ """

    @abstractmethod
    async def play(self, track_id: str) -> bool:
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


def auto_memorize_tracks(func: Callable[..., AsyncIterator[Track]]):
    if not isasyncgenfunction(func):
        raise ValueError('Not an async iterator')

    @wraps(func)
    async def wrapper(*args, **kwargs) -> AsyncIterator[Track]:
        tracks_to_save: list[Track] = []

        async for track in func(*args, **kwargs):
            yield track

            if not isinstance(track, Track):
                continue

            tracks_to_save.append(track)

        if not tracks_to_save:
            return

        await db.cache_track_objects(tracks_to_save)

    return wrapper
