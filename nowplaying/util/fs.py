from pathlib import Path
from tempfile import gettempdir

from .string import random_string


ROOT_DIR = Path(__file__).parent.parent.parent


def temp_file(suffix: str = '') -> Path:
    return Path(gettempdir()) / (random_string(15) + suffix)
