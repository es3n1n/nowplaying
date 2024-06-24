from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse

from .bot.handlers.exceptions import send_auth_code_error
from .core.config import config
from .core.database import db
from .core.sign import SIGN_EXPIRED_EXCEPTION
from .enums.start_actions import StartAction
from .exceptions.platforms import PlatformInvalidAuthCodeError
from .routes.ext import router as ext_router
from .util.fs import ROOT_DIR
from .util.http import STATUS_TEMPORARY_REDIRECT, is_clientside_error


app = FastAPI(
    openapi_url=None,
    redoc_url=None,
    docs_url=None,
)
app.include_router(ext_router)


def mount_static(web_path: str, *path) -> None:
    result_path = ROOT_DIR / 'frontend'
    for arg in path:
        result_path /= arg

    if not result_path.exists():
        raise ValueError(f'{web_path} frontend data doesnt exist')

    app.mount(web_path, StaticFiles(directory=result_path, html=True))


# todo: move to a router once it would be possible (not implemented in fastapi atm)
mount_static('/ym', 'ym', 'web-app', 'build')
mount_static('/apple', 'apple')


@app.exception_handler(PlatformInvalidAuthCodeError)
async def invalid_code_handler(_: Request, exc: PlatformInvalidAuthCodeError) -> RedirectResponse:
    await send_auth_code_error(exc)
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
