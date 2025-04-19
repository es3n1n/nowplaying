from enum import Enum, unique


@unique
class CallbackButton(str, Enum):
    PLAY_PREFIX = 'play'
    ADD_TO_QUEUE_PREFIX = 'queue'
    LOGOUT_PREFIX = 'logout'
    LOADING = 'loading'
    CONFIG_TOGGLE_PREFIX = 'toggle'
