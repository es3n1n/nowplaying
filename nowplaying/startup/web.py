from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from uvicorn import run

from nowplaying.bot.handlers.exceptions import send_auth_code_error_msg
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.core.sign import SIGN_EXPIRED_EXCEPTION
from nowplaying.enums.start_actions import StartAction
from nowplaying.exceptions.platforms import PlatformInvalidAuthCodeError
from nowplaying.routes.ext import router as ext_router
from nowplaying.util.fs import ROOT_DIR
from nowplaying.util.http import STATUS_TEMPORARY_REDIRECT, is_clientside_error
from nowplaying.util.logger import logger


app = FastAPI(
    openapi_url=None,
    redoc_url=None,
    docs_url=None,
)
app.include_router(ext_router)


def mount_static(web_path: str, *path: str) -> None:
    result_path = ROOT_DIR / 'frontend'
    for arg in path:
        result_path /= arg

    if not result_path.exists():
        raise FileNotFoundError(web_path)

    app.mount(web_path, StaticFiles(directory=result_path, html=True))


# TODO(es3n1n): move to a router once it would be possible (not implemented in fastapi atm)
mount_static('/ym', 'ym', 'web-app', 'build')
mount_static('/apple', 'apple')


@app.exception_handler(PlatformInvalidAuthCodeError)
async def invalid_code_handler(_: Request, exc: PlatformInvalidAuthCodeError) -> RedirectResponse:
    await send_auth_code_error_msg(exc)
    return RedirectResponse(
        url=config.BOT_URL,
        status_code=STATUS_TEMPORARY_REDIRECT,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> ORJSONResponse | RedirectResponse:
    is_session_expired: bool = (
        exc.status_code == SIGN_EXPIRED_EXCEPTION.status_code and exc.detail == SIGN_EXPIRED_EXCEPTION.detail
    )
    if is_clientside_error(exc.status_code):
        redirect_to = config.BOT_URL

        if is_session_expired:
            redirect_to = config.bot_plain_start_url(StartAction.SIGN_EXPIRED)

        return RedirectResponse(
            url=redirect_to,
            status_code=STATUS_TEMPORARY_REDIRECT,
        )

    return ORJSONResponse(content={'detail': exc.detail}, status_code=exc.status_code)


# We **have** to initialize the pool from `on_event` callback, otherwise we'll get transaction errors :shrug:
@app.on_event('startup')
async def startup() -> None:
    await db.init()


def start_web() -> None:
    kw = {}
    if not config.is_dev_env:
        kw['workers'] = config.WEB_WORKERS

    # Start the web server
    logger.info('Starting web-server...')
    run(
        'nowplaying.startup.web:app',
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        **kw,  # type: ignore[arg-type]
    )
