from asyncio import run as asyncio_run
from multiprocessing import Process

from aiogram.types import BotCommand
from uvicorn import run

from .bot import import_bot_handlers
from .bot.bot import bot, dp
from .core.config import config
from .core.database import db
from .util.logger import logger


async def async_start_bot() -> None:
    logger.info('Setting up bot commands')
    await bot.set_my_commands(commands=[
        BotCommand(command='start', description='Start'),
        BotCommand(command='link', description='Link account'),
        BotCommand(command='logout', description='Logout from platforms'),
    ])

    logger.info('Starting long polling')
    dp.startup.register(db.init)
    await dp.start_polling(bot)


def start_bot() -> None:
    import_bot_handlers()
    asyncio_run(async_start_bot())


def main() -> None:
    # Initialize the database
    asyncio_run(db.init())

    # Start the telegram bot process
    tg_process = Process(target=start_bot)
    tg_process.start()

    kw = {}
    if not config.is_dev_env:
        kw['workers'] = config.WEB_WORKERS

    # Start the web server
    logger.info('Starting web-server...')
    run(
        'nowplaying.web_app:app', host=config.WEB_HOST, port=config.WEB_PORT,
        **kw,  # type: ignore
    )


if __name__ == '__main__':
    main()
