from collections.abc import Iterator
from pathlib import Path
from time import sleep, time

from . import FILE_LIFE_TIME, JOB_INTERVAL, TELEGRAM_BOT_API_WORKDIR_PATH, err, info


class FileJanitor:
    def __init__(self, workdir: Path) -> None:
        self.workdir = workdir
        self.cleanup_dirs: tuple[str, ...] = ('music',)

    def clean(self) -> None:
        if not self._verify_workdir():
            err('Workdir is not valid, skipping cleanup')
            return

        info('Starting janitor job')
        for bot_dir in self._get_bot_directories():
            self._process_bot_directory(bot_dir)

    def _verify_workdir(self) -> bool:
        if not self.workdir.exists():
            err(f'Workdir {self.workdir} does not exist')
            return False
        return True

    def _get_bot_directories(self) -> Iterator[Path]:
        return (d for d in self.workdir.iterdir() if d.is_dir())

    def _process_bot_directory(self, bot_dir: Path) -> None:
        bot_id = bot_dir.name.split(':')[0]
        info(f'Processing bot directory {bot_id}')

        for dir_name in self.cleanup_dirs:
            directory = bot_dir / dir_name
            if directory.exists():
                self._cleanup_directory(directory)

    def _cleanup_directory(self, directory: Path) -> None:
        info(f'Cleaning up {directory.name}')
        current_time = int(time())

        for file in directory.iterdir():
            if not file.is_file():
                continue

            if not self._is_file_expired(file, current_time):
                continue

            try:
                file.unlink()
                err(f'Removed outdated file {file.name}')
            except OSError as e:
                err(f'Failed to remove file {file.name}: {e}')

    @staticmethod
    def _is_file_expired(file: Path, current_time: float) -> bool:
        try:
            mtime = file.stat().st_mtime
        except OSError as e:
            err(f'Failed to get mtime for file {file.name}: {e}')
            return False

        if current_time - mtime < FILE_LIFE_TIME:
            info(f'File {file.name} is not old enough yet (age: {current_time - mtime})')
            return False

        return True


def run_janitor() -> None:
    janitor = FileJanitor(TELEGRAM_BOT_API_WORKDIR_PATH)

    while True:
        try:
            janitor.clean()
        except Exception as e:  # noqa: BLE001
            err(f'Unexpected error during cleanup: {e}')

        sleep(JOB_INTERVAL)


if __name__ == '__main__':
    run_janitor()
