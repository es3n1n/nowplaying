import asyncio
import types
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any


class AutoRemovingLock:
    def __init__(self, parent_dict: dict[str, 'AutoRemovingLock'], key: str) -> None:
        self.lock = asyncio.Lock()
        self.parent_dict = parent_dict
        self.key = key

    async def __aenter__(self) -> 'AutoRemovingLock':
        """Forward the call to the lock."""
        await self.lock.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None
    ) -> None:
        """Forward the call to the lock and remove it from the parent dict if no one else is waiting for it."""
        await self.lock.__aexit__(exc_type, exc_val, exc_tb)

        # If no one else is waiting for this lock, remove it from the parent dict
        if self.lock.locked():
            return

        if self.key in self.parent_dict:
            del self.parent_dict[self.key]


class LockManager:
    def __init__(self) -> None:
        self._rw_lock = asyncio.Lock()
        self.locks: dict[str, AutoRemovingLock] = {}

    def is_locked(self, key: str) -> bool:
        return key in self.locks and self.locks[key].lock.locked()

    @asynccontextmanager
    async def lock(self, key: str) -> AsyncGenerator[AutoRemovingLock, Any]:
        async with self._rw_lock:
            if key not in self.locks:
                self.locks[key] = AutoRemovingLock(self.locks, key)
            lock = self.locks[key]

        try:
            await lock.__aenter__()
            yield lock
        finally:
            await lock.__aexit__(None, None, None)
