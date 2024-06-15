from asyncio import run as asyncio_run
from multiprocessing import Process

from aiogram.types import BotCommand
from fastapi import Request
from fastapi.responses import ORJSONResponse, RedirectResponse
from starlette.exceptions import HTTPException
from uvicorn import run

from . import app
from .bot.bot import bot, dp
from .core.config import config
from .util.logger import get_uvicorn_config, logger


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> ORJSONResponse | RedirectResponse:
    if 400 <= exc.status_code <= 499:
        return RedirectResponse(
            url=config.BOT_URL,
            status_code=307,
        )

    return ORJSONResponse(content={'detail': exc.detail}, status_code=exc.status_code)


def start_bot() -> None:
    async def _start() -> None:
        logger.info('Setting up bot commands')
        await bot.set_my_commands(commands=[
            BotCommand(command='link', description='Link spotify account')
        ])

        logger.info('Starting long polling')
        await dp.start_polling(bot)

    asyncio_run(_start())


def main() -> None:
    process = Process(target=start_bot)
    process.start()

    kw = {}

    if not config.dev_env:
        kw['workers'] = config.WEB_WORKERS

    logger.info('Starting web-server...')
    run('nowplaying:app', host=config.WEB_HOST, port=config.WEB_PORT,
        log_config=get_uvicorn_config(), **kw)  # type: ignore


if __name__ == '__main__':
    main()
