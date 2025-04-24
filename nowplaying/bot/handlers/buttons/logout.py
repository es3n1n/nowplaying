from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot
from nowplaying.core.database import db
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.util.string import extract_from_query


async def handle_logout_button(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError

    config = await db.get_user_config(query.from_user.id)
    command, platform_name = extract_from_query(query.data, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if await db.delete_user_token(query.from_user.id, platform_type):
        await bot.answer_callback_query(query.id, text=config.text('Successfully logged out'))
        return

    await bot.answer_callback_query(query.id, text=config.text('Unable to logout, are you sure you are authorized?'))
