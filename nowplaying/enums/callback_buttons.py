from enum import Enum, unique


@unique
class CallbackButtons(str, Enum):  # noqa: WPS600
    PLAY_PREFIX = 'play'
    ADD_TO_QUEUE_PREFIX = 'queue'
    LOGOUT_PREFIX = 'logout'
    LOADING = 'loading'
