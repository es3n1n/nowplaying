from importlib import resources
from pathlib import Path
from shutil import rmtree

from grpc_tools import protoc

from google.api import annotations_pb2


cwd = Path(__file__).resolve().absolute().parent
root = cwd.parent
ynison = root / 'nowplaying' / 'external' / 'ynison'

protos_dir = ynison / 'proto'
out_dir = ynison / 'pyproto'

if out_dir.is_dir():
    rmtree(out_dir)

out_dir.mkdir()

file_name = (resources.files('grpc_tools') / '_proto').resolve()
googleapis_dir = Path(annotations_pb2.__file__).parents[2]

for proto in protos_dir.glob('*.proto'):
    base_includes = [
        f'-I{protos_dir.absolute()!s}',
        f'-I{protos_dir.absolute()!s}',
        f'-I{googleapis_dir.absolute()!s}',
        f'-I{file_name.absolute()!s}',
    ]

    def invoke(*args: str, includes: list[str] = base_includes) -> None:
        args = [*includes, *args]
        print('+ python -m grpc_tools.protoc ' + ' '.join(args))  # noqa: T201
        protoc.main(args)

    invoke(
        # Generate grpc
        f'--grpc_python_out={out_dir.absolute()!s}',
        # Generate protobuf
        f'--pyi_out={out_dir.absolute()!s}',
        f'--python_out={out_dir.absolute()!s}',
        str(proto.absolute()),
    )


for generated_file in out_dir.iterdir():
    if not generated_file.is_file():
        continue

    lines = generated_file.read_text().splitlines()

    for i, line in enumerate(lines):
        if not line.startswith('import'):
            continue

        if 'google' in line or '_pb2' not in line:
            continue

        # Transform "import queue_pb2 as _queue_pb2"
        # to "from . import queue_pb2 as _queue_pb2"
        lines[i] = f'from . {line}'

    generated_file.write_text('\n'.join(lines))


(out_dir / '__init__.py').open('w').close()
