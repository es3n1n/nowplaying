from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from nowplaying.bot.bot import dp
from nowplaying.core.database import db
from nowplaying.enums.callback_buttons import CallbackButton
from nowplaying.util.string import chunks, encode_query


@dp.message(Command('logout', ignore_case=True))
async def link_command_handler(message: Message) -> None:
    if message.from_user is None:
        raise ValueError

    kb = [
        InlineKeyboardButton(
            text=f'Logout from {platform.value.capitalize()}',
            callback_data=encode_query(CallbackButton.LOGOUT_PREFIX, platform.value),
        )
        for platform in await db.get_user_authorized_platforms(message.from_user.id)
    ]

    if not kb:
        await message.reply('You are not authorized in any platform')
        return

    await message.reply(
        'Click on the buttons below to logout',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=chunks(kb, 2),
        ),
    )
