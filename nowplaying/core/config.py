from base64 import b64decode, b64encode

from pydantic_settings import BaseSettings, SettingsConfigDict

from ..util.fs import ROOT_DIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8'
    )

    ENVIRONMENT: str = 'production'

    EMPTY_MP3_FILE_URL: str = 'https://es3n1n.eu/empty.mp3'

    BOT_TOKEN: str
    BOT_CACHE_CHAT_ID: int
    BOT_URL: str = 'https://t.me/playinnowbot'

    STATE_SECRET: str

    WEB_HOST: str = '0.0.0.0'
    WEB_PORT: int = 1337
    WEB_WORKERS: int = 2

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_SECRET: str
    SPOTIFY_REDIRECT_URL: str

    POSTGRES_ADDRESS: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def db_connection_info(self) -> str:
        return f'dbname={self.POSTGRES_DB} '\
               f'user={self.POSTGRES_USER} '\
               f'password={self.POSTGRES_PASSWORD} '\
               f'host={self.POSTGRES_ADDRESS} '\
               f'port={self.POSTGRES_PORT}'

    @property
    def dev_env(self):
        return self.ENVIRONMENT.lower() in ['dev', 'development']

    def get_start_url(self, payload: str) -> str:
        return config.BOT_URL + '?start=' + b64encode(payload.encode()).decode().rstrip('=')

    def decode_start_url(self, payload: str) -> str | None:
        try:
            return b64decode(payload).decode()
        except ValueError:
            return None


config = Settings()  # type: ignore
