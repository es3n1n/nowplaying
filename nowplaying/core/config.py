from base64 import b64decode, b64encode

from pydantic_settings import BaseSettings, SettingsConfigDict

from ..util.fs import ROOT_DIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8'
    )

    ENVIRONMENT: str = 'production'

    WEB_SERVER_PUBLIC_ENDPOINT: str = 'https://now.es3n1n.eu'

    EMPTY_MP3_FILE_URL: str = 'https://es3n1n.eu/empty.mp3'
    DEEZER_ARL_COOKIE: str

    BOT_DEV_CHAT_ID: int = 1490827215
    BOT_TOKEN: str
    BOT_CACHE_CHAT_ID: int = 1490827215
    BOT_URL: str = 'https://t.me/playinnowbot'

    STATE_SECRET: str

    WEB_HOST: str = '0.0.0.0'
    WEB_PORT: int = 1337
    WEB_WORKERS: int = 2

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_SECRET: str
    SPOTIFY_REDIRECT_URL: str

    LASTFM_API_KEY: str
    LASTFM_SHARED_SECRET: str
    LASTFM_REDIRECT_URL: str

    APPLE_SECRET_KEY: str
    APPLE_KEY_ID: str
    APPLE_TEAM_ID: str

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
        # fixme @es3n1n: ghetto workaround for paddings, we can't use = in start payload because telegram doesn't allows
        try:
            return b64decode(payload + ('=' * 3)).decode()
        except ValueError:
            return None


config = Settings()  # type: ignore
