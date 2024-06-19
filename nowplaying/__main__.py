from asyncio import run as asyncio_run
from multiprocessing import Process

from aiogram.types import BotCommand
from fastapi import Request
from fastapi.responses import ORJSONResponse, RedirectResponse
from starlette.exceptions import HTTPException
from uvicorn import run

from . import app
from .bot.bot import bot, dp
from .bot.handlers.exceptions import send_auth_code_error
from .core.config import config
from .exceptions.platforms import PlatformInvalidAuthCodeError
from .util.logger import logger


@app.exception_handler(PlatformInvalidAuthCodeError)
async def invalid_code_handler(_: Request, exc: PlatformInvalidAuthCodeError) -> RedirectResponse:
    await send_auth_code_error(exc)
    return RedirectResponse(
        url=config.BOT_URL,
        status_code=307,
    )


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
            BotCommand(command='start', description='Start'),
            BotCommand(command='link', description='Link account'),
            BotCommand(command='logout', description='Logout from platforms'),
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
        **kw)  # type: ignore


if __name__ == '__main__':
    main()
