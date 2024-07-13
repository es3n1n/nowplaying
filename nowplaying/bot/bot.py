from aiogram import Bot, Dispatcher

from ..core.config import config
from .session import BotSession


dp = Dispatcher()
bot = Bot(token=config.BOT_TOKEN, session=BotSession())
