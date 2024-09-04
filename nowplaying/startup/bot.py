from asyncio import run

from aiogram.types import BotCommand

from nowplaying.bot import import_bot_handlers
from nowplaying.bot.bot import bot, dp
from nowplaying.core.database import db
from nowplaying.util.logger import logger


async def async_start_bot() -> None:
    logger.info('Setting up bot commands')
    await bot.set_my_commands(
        commands=[
            BotCommand(command='start', description='Start'),
            BotCommand(command='link', description='Link account'),
            BotCommand(command='logout', description='Logout from platforms'),
        ]
    )

    logger.info('Starting long polling')
    dp.startup.register(db.init)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def start_bot() -> None:
    import_bot_handlers()
    run(async_start_bot())
