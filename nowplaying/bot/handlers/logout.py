from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.database import db
from ...util.string import chunks
from ..bot import dp


@dp.message(Command('logout', ignore_case=True))
async def link_command_handler(message: Message) -> None:
    if message.from_user is None:
        raise ValueError()

    kb = []
    for platform in await db.get_user_authorized_platforms(message.from_user.id):
        kb.append(InlineKeyboardButton(
            text=f'Logout from {platform.value.capitalize()}',
            callback_data=f'logout_{platform.value}',
        ))

    if not kb:
        await message.reply('You are not authorized in any platform')
        return

    await message.reply(
        'Click on the buttons below to logout',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=chunks(kb, 2),
        ),
    )
