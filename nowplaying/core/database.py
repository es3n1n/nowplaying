from asyncpg import Pool, create_pool

from nowplaying.core.config import config
from nowplaying.core.database_init import DATABASE_INIT_SQL
from nowplaying.models.cached_local_track import CachedLocalTrack
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.user_config import UserConfig
from nowplaying.util.dns import select_hostname
from nowplaying.util.logger import logger
from nowplaying.util.worker import worker


class Database:
    def __init__(self) -> None:
        self._pool: Pool | None = None

    async def init(self) -> None:
        await self.get_pool()

    async def get_pool(self) -> Pool:
        if self._pool is None:
            logger.info('Connecting to the database')

            self._pool = await create_pool(
                host=select_hostname(config.POSTGRES_DOCKER_ADDRESS, config.POSTGRES_ADDRESS, config.POSTGRES_PORT),
                port=config.POSTGRES_PORT,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                database=config.POSTGRES_DB,
            )

            if self._pool is None:
                msg = 'pool is none'
                raise ValueError(msg)

            if not worker.is_first:
                return self._pool

            logger.info('Initializing the database')
            async with self._pool.acquire() as conn, conn.transaction():
                await conn.execute(DATABASE_INIT_SQL)

        return self._pool

    async def is_user_authorized_globally(self, telegram_id: int) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            auth_result = await conn.fetch('SELECT 1 FROM tokens WHERE telegram_id = $1 LIMIT 1', telegram_id)
            return bool(auth_result)

    async def is_user_authorized(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            auth_result = await conn.fetch(
                'SELECT 1 FROM tokens WHERE telegram_id = $1 AND platform_name = $2 LIMIT 1',
                telegram_id,
                platform.value,
            )
            return bool(auth_result)

    async def get_user_authorized_platforms(self, telegram_id: int) -> list[SongLinkPlatformType]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            platforms = await conn.fetch('SELECT (platform_name) FROM tokens WHERE telegram_id = $1', telegram_id)
            return [SongLinkPlatformType(row['platform_name']) for row in platforms]

    async def delete_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                delete_stat = await conn.fetch(
                    'DELETE FROM tokens WHERE telegram_id = $1 AND platform_name = $2 RETURNING *',
                    telegram_id,
                    platform.value,
                )
            return bool(delete_stat)

    async def store_user_token(self, telegram_id: int, platform: SongLinkPlatformType, token: str) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'INSERT INTO tokens (telegram_id, platform_name, token) VALUES ($1, $2, $3) '
                'ON CONFLICT (telegram_id, platform_name) DO UPDATE SET token = $3',
                telegram_id,
                platform.value,
                token,
            )

    async def get_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> str | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            user_token = await conn.fetchrow(
                'SELECT (token) FROM tokens WHERE telegram_id = $1 AND platform_name = $2 LIMIT 1',
                telegram_id,
                platform.value,
            )
            return None if user_token is None else user_token['token']

    async def is_file_cached(self, uri: str) -> bool:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            cached_file_result = await conn.fetch('SELECT 1 FROM cached_files WHERE spotify_uri = $1 LIMIT 1', uri)
            return bool(cached_file_result)

    async def store_cached_file(self, uri: str, file_id: str, cached_by_user_id: int | None, quality_id: str) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'INSERT INTO cached_files (uri, file_id, cached_by_user_id, quality_id) VALUES ($1, $2, $3, $4) '
                'ON CONFLICT (uri) DO UPDATE SET file_id = $2, cached_by_user_id = $3, quality_id = $4',
                uri,
                file_id,
                cached_by_user_id,
                quality_id,
            )

    async def get_cached_file(self, uri: str) -> str | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            cached_file = await conn.fetchrow('SELECT (file_id) FROM cached_files WHERE uri = $1 LIMIT 1', uri)
            return None if cached_file is None else cached_file['file_id']

    async def delete_cached_files(self, uris: list[str]) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute('DELETE FROM cached_files WHERE uri = ANY($1)', uris)

    async def store_song_link(self, song_url: str, song_link: str) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'INSERT INTO cached_song_link_urls (song_url, song_link) VALUES ($1, $2) '
                'ON CONFLICT (song_url) DO UPDATE SET song_link = $2',
                song_url,
                song_link,
            )

    async def get_song_link(self, song_url: str) -> str | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            song_link = await conn.fetchrow(
                'SELECT (song_link) FROM cached_song_link_urls WHERE song_url = $1 LIMIT 1', song_url
            )
            return None if song_link is None else song_link['song_link']

    async def cache_local_track(self, platform: SongLinkPlatformType, url: str, artist: str, name: str) -> str:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            cache_result = await conn.fetchval(
                'SELECT cache_local_track_id($1, $2, $3, $4)',
                platform.value,
                url,
                artist,
                name,
            )
            return str(cache_result[0])

    async def get_cached_local_track_info(self, our_id: str) -> CachedLocalTrack | None:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            local_track = await conn.fetchval(
                'SELECT (id, platform_name, url, artist, name) FROM local_tracks WHERE id = $1 LIMIT 1',
                our_id,
            )

        if local_track is None:
            return None

        return CachedLocalTrack(
            id=str(local_track[0]),
            platform_type=SongLinkPlatformType(local_track[1]),
            url=local_track[2],
            artist=local_track[3],
            name=local_track[4],
        )

    async def get_user_config(self, user_id: int) -> UserConfig:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                'SELECT * FROM user_configs WHERE user_id = $1 LIMIT 1',
                user_id,
            )
            if result is None:
                return UserConfig()
            return UserConfig.model_validate(dict(result))

    async def update_config_var(self, user_id: int, field: str, *, new_value: bool) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'SELECT update_user_config_value($1, $2, $3)',
                user_id,
                field,
                new_value,
            )

    async def strip_user_id_from_cached_files(self, user_id: int) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'UPDATE cached_files SET cached_by_user_id = NULL WHERE cached_by_user_id = $1',
                user_id,
            )

    async def get_cached_files_count_for_user(self, user_id: int) -> int:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM cached_files WHERE cached_by_user_id = $1',
                user_id,
            )
            return count or 0

    async def increment_sent_tracks_count(self, user_id: int) -> None:
        pool = await self.get_pool()
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute(
                'INSERT INTO user_track_stats (user_id, track_count) '
                'VALUES ($1, 1) '
                'ON CONFLICT (user_id) DO '
                'UPDATE SET track_count = user_track_stats.track_count + 1;',
                user_id,
            )

    async def get_user_sent_tracks_count(self, user_id: int) -> int:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                'SELECT track_count FROM user_track_stats WHERE user_id = $1 LIMIT 1',
                user_id,
            )
            return count or 0


db = Database()
