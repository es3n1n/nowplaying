from enum import Enum, unique


@unique
class StartAction(Enum):
    # plain
    SIGN_EXPIRED: str = 'expired'
