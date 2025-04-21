from io import BytesIO
from pathlib import Path

import pytest

from nowplaying.util.compressing import compress_to_jpeg


DATA_DIR = Path(__file__).parent / 'data'


@pytest.mark.parametrize(
    'file_name',
    reversed([pytest.param(x.name, id=x.name) for x in DATA_DIR.iterdir()]),
)
def test_compression(file_name: str) -> None:
    data = (DATA_DIR / file_name).read_bytes()
    result = compress_to_jpeg(BytesIO(data), target_size_kb=200)
    assert result.getbuffer().nbytes / 1024 <= 200
