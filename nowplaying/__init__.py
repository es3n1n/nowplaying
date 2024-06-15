from fastapi import FastAPI

from .bot import import_bot_handlers
from .routes.ext import router as ext_router


app = FastAPI(
    openapi_url=None,
    redoc_url=None,
    docs_url=None,
)
app.include_router(ext_router)
import_bot_handlers()
