from enum import IntEnum, auto, unique


@unique
class PlatformFeature(IntEnum):
    TRACK_GETTERS = auto()
    ADD_TO_QUEUE = auto()
    PLAY = auto()
