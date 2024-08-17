from functools import wraps
from inspect import isasyncgenfunction
from typing import Any, TypeVar

from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.exceptions.platforms import PlatformTokenInvalidateError


ResultTy = TypeVar('ResultTy')


def rethrow_platform_error(exception_ty: type, platform: SongLinkPlatformType):  # noqa: ANN201
    def decorator(func):  # noqa: ANN001, ANN202
        if isasyncgenfunction(func):

            @wraps(func)
            async def aiter_wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                except exception_ty as err:
                    # Assuming that first argument is `self`/`cls`
                    raise PlatformTokenInvalidateError(
                        platform=platform,
                        telegram_id=args[0].telegram_id,
                    ) from err

            return aiter_wrapper

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401, ANN002, ANN003
            try:
                return await func(*args, **kwargs)
            except exception_ty as err:  # type: ignore[misc]
                # Assuming that first argument is `self`/`cls`
                raise PlatformTokenInvalidateError(
                    platform=platform,
                    telegram_id=args[0].telegram_id,
                ) from err

        return wrapper

    return decorator
