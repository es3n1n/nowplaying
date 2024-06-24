from ..enums.platform_type import SongLinkPlatformType


class BasePlatformError(Exception):
    def __init__(self, platform: SongLinkPlatformType, telegram_id: int):
        self.platform = platform
        self.telegram_id = telegram_id


class PlatformTokenInvalidateError(BasePlatformError):
    """Token has expired, or something went wrong."""


class PlatformInvalidAuthCodeError(BasePlatformError):
    """Invalid authorization code, most likely a client side problem."""
