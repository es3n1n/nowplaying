from importlib import import_module
from pathlib import Path


def import_bot_handlers(base_package: str = 'nowplaying.bot.handlers') -> None:
    handlers_dir = Path(__file__).parent / 'handlers'
    import_handlers_recursively(handlers_dir, base_package)


def import_handlers_recursively(directory: Path, package: str) -> None:
    for directory_item in directory.iterdir():
        if directory_item.is_dir():
            sub_package = f'{package}.{directory_item.name}'
            import_handlers_recursively(directory_item, sub_package)
            continue

        if directory_item.stem == '__init__' or directory_item.suffix != '.py':
            continue

        module_path = f'{package}.{directory_item.stem}'
        import_module(module_path)
