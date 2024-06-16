from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from .bot import import_bot_handlers
from .routes.ext import router as ext_router
from .util.fs import ROOT_DIR


app = FastAPI(
    openapi_url=None,
    redoc_url=None,
    docs_url=None,
)
app.include_router(ext_router)
import_bot_handlers()

# todo: move to a router once it would be possible (not implemented in fastapi atm)
ym_frontend_path = ROOT_DIR / 'frontend' / 'ym' / 'web-app' / 'build'
if not ym_frontend_path.exists():
    raise ValueError('no ym frontend')
app.mount('/ym', StaticFiles(directory=ym_frontend_path, html=True))
