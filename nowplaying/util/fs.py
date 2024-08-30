from pathlib import Path
from os import environ


ROOT_DIR = Path(__file__).parent.parent.parent
if 'ROOT_DIR' in environ:
    ROOT_DIR = Path(environ['ROOT_DIR'])
