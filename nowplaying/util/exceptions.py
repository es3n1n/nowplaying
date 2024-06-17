from functools import wraps
from inspect import isasyncgenfunction
from typing import Any, Type, TypeVar

from ..enums.platform_type import SongLinkPlatformType
from ..exceptions.platforms import PlatformTokenInvalidateError


ResultTy = TypeVar('ResultTy')


def rethrow_platform_error(exception_ty: Type, platform: SongLinkPlatformType):
    def decorator(func):
        if isasyncgenfunction(func):
            @wraps(func)
            async def async_generator_wrapper(*args, **kwargs):
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                except exception_ty:
                    # Assuming that first argument is `self`/`cls`
                    raise PlatformTokenInvalidateError(
                        platform=platform,
                        telegram_id=args[0].telegram_id
                    )

            return async_generator_wrapper

        @wraps(func)
        async def async_function_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except exception_ty:
                # Assuming that first argument is `self`/`cls`
                raise PlatformTokenInvalidateError(
                    platform=platform,
                    telegram_id=args[0].telegram_id
                )

        return async_function_wrapper

    return decorator
