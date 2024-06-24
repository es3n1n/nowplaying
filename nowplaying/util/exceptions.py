from functools import wraps
from inspect import isasyncgenfunction
from typing import Any, Type, TypeVar

from ..enums.platform_type import SongLinkPlatformType
from ..exceptions.platforms import PlatformTokenInvalidateError


ResultTy = TypeVar('ResultTy')


def rethrow_platform_error(exception_ty: Type, platform: SongLinkPlatformType):  # noqa: WPS231
    def decorator(func):  # noqa: WPS231
        if isasyncgenfunction(func):
            @wraps(func)
            async def aiter_wrapper(*args, **kwargs):  # noqa: WPS430
                try:
                    async for item in func(*args, **kwargs):  # noqa: WPS110
                        yield item  # noqa: WPS220
                except exception_ty:
                    # Assuming that first argument is `self`/`cls`
                    raise PlatformTokenInvalidateError(
                        platform=platform,
                        telegram_id=args[0].telegram_id,
                    )

            return aiter_wrapper

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except exception_ty:
                # Assuming that first argument is `self`/`cls`
                raise PlatformTokenInvalidateError(
                    platform=platform,
                    telegram_id=args[0].telegram_id,
                )

        return wrapper

    return decorator
