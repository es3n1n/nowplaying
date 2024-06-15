from importlib import import_module
from pathlib import Path


def import_bot_handlers() -> None:
    handlers_dir = Path(__file__).parent / 'handlers'

    for file in handlers_dir.glob('*.py'):
        import_module(f'nowplaying.bot.handlers.{file.stem}')
