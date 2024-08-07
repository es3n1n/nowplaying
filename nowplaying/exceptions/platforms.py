from ..enums.platform_type import SongLinkPlatformType


class BasePlatformError(Exception):
    def __init__(self, platform: SongLinkPlatformType):
        self.platform = platform


class BasePlatformWithIDError(BasePlatformError):
    def __init__(self, platform: SongLinkPlatformType, telegram_id: int):
        super().__init__(platform)
        self.telegram_id = telegram_id


class PlatformTokenInvalidateError(BasePlatformWithIDError):
    """The token has expired, or something went wrong."""


class PlatformInvalidAuthCodeError(BasePlatformWithIDError):
    """Invalid authorization code, most likely a client side problem."""


class PlatformTemporarilyUnavailableError(BasePlatformError):
    """The platform is down, there's nothing we can do."""
