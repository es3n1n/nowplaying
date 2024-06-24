from pathlib import Path
from tempfile import gettempdir

from .string import random_string


ROOT_DIR = Path(__file__).parent.parent.parent
TEMP_FILE_NAME_SIZE: int = 15


def temp_file(suffix: str = '') -> Path:
    return Path(gettempdir()) / (random_string(TEMP_FILE_NAME_SIZE) + suffix)
