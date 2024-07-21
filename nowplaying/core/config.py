from base64 import b64decode, b64encode
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..enums.start_actions import StartAction
from ..util.fs import ROOT_DIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    ENVIRONMENT: str = 'production'

    DEVELOPER_USERNAME: str = 'invlpg'

    WEB_SERVER_PUBLIC_ENDPOINT: Annotated[str, Field(validate_default=True)] = 'https://now.es3n1n.eu'

    EMPTY_MP3_FILE_URL: Annotated[str, Field(validate_default=True)] = 'https://es3n1n.eu/empty.mp3'
    DEEZER_ARL_COOKIE: str

    BOT_DEV_CHAT_ID: int = 1490827215
    BOT_TOKEN: str
    BOT_CACHE_CHAT_ID: int = 1490827215
    BOT_URL: Annotated[str, Field(validate_default=True)] = 'https://t.me/playinnowbot'
    BOT_LOG_REQUESTS: bool = False
    BOT_TELEGRAM_ERROR_REPORTING: bool = True

    STATE_SECRET: str

    WEB_HOST: str = '0.0.0.0'  # noqa: S104
    WEB_PORT: int = 1337
    WEB_WORKERS: int = 2

    YOUTUBE_COOKIES_PATH: str | None = None

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_SECRET: str

    LASTFM_API_KEY: str
    LASTFM_SHARED_SECRET: str

    APPLE_SECRET_KEY: str
    APPLE_KEY_ID: str
    APPLE_TEAM_ID: str

    POSTGRES_ADDRESS: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @field_validator('WEB_SERVER_PUBLIC_ENDPOINT', 'EMPTY_MP3_FILE_URL', 'BOT_URL')
    @classmethod
    def validate_url(cls, val_to_validate: str) -> str:
        return val_to_validate.rstrip('/')

    @field_validator('YOUTUBE_COOKIES_PATH')
    @classmethod
    def validate_path(cls, path: str | None) -> str | None:
        if not path:
            return None

        if Path(path).exists():
            return path

        out_path = ROOT_DIR / path
        if not out_path.exists():
            raise ValueError(f'{out_path} file does not exist')

        return str(out_path.resolve().absolute())

    def bot_plain_start_url(self, payload: str | StartAction) -> str:
        payload_str: str = payload if isinstance(payload, str) else payload.value
        return f'{self.BOT_URL}?start={payload_str}'

    @property
    def is_dev_env(self):
        return self.ENVIRONMENT.lower() in {'dev', 'development'}

    def redirect_url_for_ext_svc(self, svc_name: str) -> str:
        return f'{self.WEB_SERVER_PUBLIC_ENDPOINT}/ext/{svc_name}/callback'

    def get_start_url(self, payload: str) -> str:
        payload_encoded = b64encode(payload.encode()).decode().rstrip('=')
        return f'{self.BOT_URL}?start={payload_encoded}'

    @staticmethod
    def decode_start_url(payload: str) -> str | None:  # noqa: WPS602
        # fixme @es3n1n: ghetto workaround for paddings, we can't use = in start payload because telegram doesn't allow
        #   them
        try:
            return b64decode(payload + ('=' * 3)).decode()
        except ValueError:
            return None

    @property
    def deezer_apl_cookie_set(self) -> bool:
        return self.DEEZER_ARL_COOKIE not in {'', '1'}


config = Settings()  # type: ignore
