from pathlib import Path
from tempfile import NamedTemporaryFile


ROOT_DIR = Path(__file__).parent.parent.parent


def temp_file(suffix: str | None = None) -> Path:
    result = NamedTemporaryFile(suffix=suffix)
    result.close()
    return Path(result.name)
