from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.spotify import spotify
from ..bot import dp


@dp.message(Command('link', ignore_case=True))
async def link_command_handler(message: Message) -> None:
    assert message.from_user is not None

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Authorize', url=spotify.get_authorization_url(message.from_user.id))]
    ])

    await message.reply('Click on the button below to authorize in spotify', reply_markup=kb)
