from psycopg import connect

from ..core.config import config
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

    def is_user_authorized(self, telegram_id: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM spotify_tokens WHERE telegram_id = %s LIMIT 1', (telegram_id,))

            if cur.fetchone() is None:
                return False
            return True

    def store_user_token(self, telegram_id: int, spotify_token: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO spotify_tokens (telegram_id, spotify_token) VALUES (%s, %s) ON CONFLICT (telegram_id) DO '
                'UPDATE SET spotify_token = %s',
                (telegram_id, spotify_token, spotify_token,),
            )
            self.conn.commit()

    def get_user_token(self, telegram_id: int) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT (spotify_token) FROM spotify_tokens WHERE telegram_id = %s LIMIT 1',
                (telegram_id,)
            )

            r = cur.fetchone()
            return r[0] if r is not None else None


db = Database()
