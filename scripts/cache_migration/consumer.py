import asyncio

from nowplaying.core.database import db
from nowplaying.bot.bot import bot, dp
from nowplaying.core.config import config
from nowplaying.util.logger import logger
from aiogram import types
from aiogram.filters import Filter
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
    await db.store_cached_file(track_uri, message.audio.file_id)
    logger.info(f'Cached file for {track_uri} ({message.audio.file_name})')


async def main() -> None:
    dp.startup.register(db.init)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
