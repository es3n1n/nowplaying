from typing import Optional

from filelock import FileLock, Timeout


class Worker:
    def __init__(self) -> None:
        self.lock: Optional[FileLock] = None
        self.setup('web')

    def setup(self, service_name: str) -> None:
        self.lock = FileLock(f'worker-{service_name}.lock')
        try:
            self.lock.acquire(blocking=False)
        except Timeout:
            pass

    @property
    def is_first(self) -> bool:
        assert self.lock is not None
        return self.lock.is_locked


worker = Worker()
