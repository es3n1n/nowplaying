from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse

from .bot.handlers.exceptions import send_auth_code_error
from .core.config import config
from .core.database import db
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

# todo: move to a router once it would be possible (not implemented in fastapi atm)
ym_frontend_path = ROOT_DIR / 'frontend' / 'ym' / 'web-app' / 'build'
if not ym_frontend_path.exists():
    raise ValueError('no ym frontend')
app.mount('/ym', StaticFiles(directory=ym_frontend_path, html=True))


@app.exception_handler(PlatformInvalidAuthCodeError)
async def invalid_code_handler(_: Request, exc: PlatformInvalidAuthCodeError) -> RedirectResponse:
    await send_auth_code_error(exc)
    return RedirectResponse(
        url=config.BOT_URL,
        status_code=STATUS_TEMPORARY_REDIRECT,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> ORJSONResponse | RedirectResponse:
    if is_clientside_error(exc.status_code):
        return RedirectResponse(
            url=config.BOT_URL,
            status_code=STATUS_TEMPORARY_REDIRECT,
        )

    return ORJSONResponse(content={'detail': exc.detail}, status_code=exc.status_code)


# We **have** to initialize the pool from `on_event` callback, otherwise we'll get transaction errors :shrug:
@app.on_event('startup')
async def startup() -> None:
    await db.init()
