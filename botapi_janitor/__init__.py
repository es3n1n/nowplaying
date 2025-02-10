from os import environ
from pathlib import Path
from sys import stderr, stdout


JOB_INTERVAL = int(environ.get('JANITOR_JOB_INTERVAL', str(10 * 60)))
FILE_LIFE_TIME = int(environ.get('JANITOR_FILE_LIFE_TIME', str(5 * 60)))
TELEGRAM_BOT_API_WORKDIR_PATH = Path(environ.get('JANITOR_WORKDIR', '/var/lib/telegram-bot-api'))


def info(msg: str) -> None:
    stdout.write(f'[INFO] {msg}\n')
    stdout.flush()


def err(msg: str) -> None:
    stderr.write(f'[ERR] {msg}\n')
    stderr.flush()
