import asyncio

from nowplaying.core.database import db
from nowplaying.bot.bot import bot, dp
from nowplaying.core.config import config
from nowplaying.util.logger import logger
from aiogram import types
from aiogram.filters import Filter, CommandStart
from os import environ


config.LOCAL_TELEGRAM_API_BASE_URL = 'http://127.0.0.1:8081'
PRODUCER_TELEGRAM_ID = int(environ['PRODUCER_TELEGRAM_ID'])


class CachedTrackFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        if message.audio is None or message.from_user is None:
            return False
        return message.from_user.id == PRODUCER_TELEGRAM_ID


@dp.message(CachedTrackFilter())
async def on_cached_track_recv(message: types.Message) -> None:
    if message.caption is None or message.audio is None:
        logger.error('Cached track message has no caption or track')
        return

    track_uri = message.caption.split()[0].lstrip('#')
    user_id_str = message.caption.split()[1].lstrip('#uid_')
    user_id = int(user_id_str) if user_id_str != 'None' else None

    if '#khz_' in message.caption:
        exc_msg = 'implement #q'
        raise ValueError(exc_msg)

    await db.store_cached_file(track_uri, message.audio.file_id, user_id, {})  # type: ignore[typeddict-item]
    if user_id:
        await db.increment_sent_tracks_count(user_id)
    logger.info(f'Cached file for {track_uri} ({message.audio.file_name}) received from {user_id}')


@dp.message(CommandStart())
async def on_start(message: types.Message) -> None:
    if message.from_user is None or message.from_user.id != PRODUCER_TELEGRAM_ID:
        return

    logger.info('Initializing database')
    pool = await db.get_pool()
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute('DELETE FROM user_track_stats')
        await conn.execute('DELETE FROM cached_files')


async def main() -> None:
    dp.startup.register(db.init)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
