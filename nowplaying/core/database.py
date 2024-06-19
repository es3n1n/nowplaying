from typing import Any

from psycopg import connect

from ..core.config import config
from ..models.cached_local_track import CachedLocalTrack
from ..models.song_link import SongLinkPlatformType
from ..util.fs import ROOT_DIR
from ..util.logger import logger
from ..util.worker import worker


init_sql = (ROOT_DIR / 'init.sql').read_text()


class Database:
    def __init__(self):
        logger.info('Connecting to the database')
        self.conn = connect(
            config.db_connection_info,
        )

        if worker.is_first:
            with self.conn.cursor() as cur:
                cur.execute(init_sql)
                self.conn.commit()

    @staticmethod
    def _first_or_none(var: tuple | None) -> Any | None:
        return var[0] if var is not None else None

    def is_user_authorized_globally(self, telegram_id: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM tokens WHERE telegram_id = %s LIMIT 1',
                        (telegram_id,))
            return cur.fetchone() is not None

    def is_user_authorized(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM tokens WHERE telegram_id = %s AND platform_name = %s LIMIT 1',
                        (telegram_id, platform.value,))
            return cur.fetchone() is not None

    def get_user_authorized_platforms(self, telegram_id: int) -> list[SongLinkPlatformType]:
        with self.conn.cursor() as cur:
            cur.execute('SELECT (platform_name) FROM tokens WHERE telegram_id = %s', (telegram_id,))
            return [SongLinkPlatformType(x[0]) for x in cur.fetchall()]

    def delete_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> bool:
        with self.conn.cursor() as cur:
            cur.execute('DELETE FROM tokens WHERE telegram_id = %s AND platform_name = %s',
                        (telegram_id, platform.value))
            success = cur.rowcount >= 1
            if success:
                self.conn.commit()
            return success

    def store_user_token(self, telegram_id: int, platform: SongLinkPlatformType, token: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO tokens (telegram_id, platform_name, token) VALUES (%s, %s, %s) '
                'ON CONFLICT (telegram_id, platform_name) DO UPDATE SET token = %s',
                (telegram_id, platform.value, token, token,),
            )
            self.conn.commit()

    def get_user_token(self, telegram_id: int, platform: SongLinkPlatformType) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT (token) FROM tokens WHERE telegram_id = %s AND platform_name = %s LIMIT 1',
                (telegram_id, platform.value,)
            )
            return self._first_or_none(cur.fetchone())

    def is_file_cached(self, spotify_uri: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM cached_files WHERE spotify_uri = %s LIMIT 1', (spotify_uri,))
            return cur.fetchone() is not None

    def store_cached_file(self, uri: str, file_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO cached_files (uri, file_id) VALUES (%s, %s) ON CONFLICT (uri) DO '
                'UPDATE SET file_id = %s',
                (uri, file_id, file_id,),
            )
            self.conn.commit()

    def get_cached_file(self, uri: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT (file_id) FROM cached_files WHERE uri = %s LIMIT 1',
                (uri,)
            )
            return self._first_or_none(cur.fetchone())

    def cache_local_track(self, platform: SongLinkPlatformType, url: str, artist: str, name: str) -> str:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT cache_local_track_id(%s, %s, %s, %s)',
                (platform.value, url, artist, name)
            )
            uuid, inserted = cur.fetchone()[0]
            if inserted == 't':
                self.conn.commit()
            return uuid

    def get_cached_local_track_info(self, our_id: str) -> CachedLocalTrack | None:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT (id, platform_name, url, artist, name) '
                'FROM local_tracks '
                'WHERE id = %s LIMIT 1',
                (our_id,)
            )
            result = self._first_or_none(cur.fetchone())
            if result is None:
                return None

            return CachedLocalTrack(
                id=result[0],
                platform_type=SongLinkPlatformType(result[1]),
                url=result[2],
                artist=result[3],
                name=result[4],
            )


db = Database()
