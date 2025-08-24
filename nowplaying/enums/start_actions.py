from enum import Enum, unique


@unique
class StartAction(Enum):
    SIGN_EXPIRED = 'expired'
