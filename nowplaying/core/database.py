from asyncpg import Pool, create_pool

from ..core.config import config
from ..models.cached_local_track import CachedLocalTrack
from ..models.song_link import SongLinkPlatformType
from ..util.fs import ROOT_DIR
from ..util.logger import logger
from ..util.worker import worker


init_sql = (ROOT_DIR / 'init.sql').read_text()


class Database:
    def __init__(self) -> None:
        self._pool: Pool | None = None

    async def get_pool(self) -> Pool:
        if self._pool is None:
            logger.info('Connecting to the database')

            self._pool = await create_pool(
                host=config.POSTGRES_ADDRESS,
                port=config.POSTGRES_PORT,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                database=config.POSTGRES_DB,
                max_size=16,
            )

            assert self._pool is not None

            if worker.is_first:
                logger.info('Initializing the database')
                async with self._pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute(init_sql)

        return self._pool

    async def is_user_authorized_globally(self, telegram_id: int) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT 1 FROM tokens WHERE telegram_id = $1 LIMIT 1', telegram_id)
            return len(result) > 0

    async def is_user_authorized(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT 1 FROM tokens WHERE telegram_id = $1 AND platform_name = $2 LIMIT 1',
                                      telegram_id, platform.value)
            return len(result) > 0

    async def get_user_authorized_platforms(self, telegram_id: int) -> list[SongLinkPlatformType]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT (platform_name) FROM tokens WHERE telegram_id = $1', telegram_id)
            return [SongLinkPlatformType(x['platform_name']) for x in result]

    async def delete_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetch('DELETE FROM tokens WHERE telegram_id = $1 AND platform_name = $2 '
                                          'RETURNING *', telegram_id, platform.value)
            return len(result) > 0

    async def store_user_token(self, telegram_id: int, platform: SongLinkPlatformType, token: str) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('INSERT INTO tokens (telegram_id, platform_name, token) VALUES ($1, $2, $3) '
                                   'ON CONFLICT (telegram_id, platform_name) DO UPDATE SET token = $3',
                                   telegram_id, platform.value, token)

    async def get_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> str | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow('SELECT (token) FROM tokens WHERE telegram_id = $1 AND platform_name = $2 '
                                         'LIMIT 1', telegram_id, platform.value)
            return None if result is None else result['token']

    async def is_file_cached(self, uri: str) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT 1 FROM cached_files WHERE spotify_uri = $1 LIMIT 1', uri)
            return len(result) > 0

    async def store_cached_file(self, uri: str, file_id: str) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('INSERT INTO cached_files (uri, file_id) VALUES ($1, $2) ON CONFLICT (uri) DO '
                                   'UPDATE SET file_id = $2', uri, file_id)

    async def get_cached_file(self, uri: str) -> str | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow('SELECT (file_id) FROM cached_files WHERE uri = $1 LIMIT 1', uri)
            return None if result is None else result['file_id']

    async def cache_local_track(self, platform: SongLinkPlatformType, url: str, artist: str, name: str) -> str:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval('SELECT cache_local_track_id($1, $2, $3, $4)',
                                         platform.value, url, artist, name)
            return str(result[0])

    async def get_cached_local_track_info(self, our_id: str) -> CachedLocalTrack | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval('SELECT (id, platform_name, url, artist, name) '
                                         'FROM local_tracks '
                                         'WHERE id = $1 LIMIT 1', our_id)

        if result is None:
            return None

        return CachedLocalTrack(
            id=str(result[0]),
            platform_type=SongLinkPlatformType(result[1]),
            url=result[2],
            artist=result[3],
            name=result[4]
        )


db = Database()
