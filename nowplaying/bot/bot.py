from aiogram import Bot, Dispatcher

from ..core.config import config


dp = Dispatcher()
bot = Bot(token=config.BOT_TOKEN)
