from ..enums.platform_type import SongLinkPlatformType


class BasePlatformException(Exception):
    def __init__(self, platform: SongLinkPlatformType, telegram_id: int):
        self.platform = platform
        self.telegram_id = telegram_id


class PlatformTokenInvalidateError(BasePlatformException):
    pass


class PlatformInvalidAuthCodeError(BasePlatformException):
    pass
