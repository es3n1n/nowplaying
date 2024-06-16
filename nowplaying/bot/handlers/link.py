from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.sign import sign
from ...platforms import platforms
from ...util.string import chunks
from ..bot import dp


async def get_auth_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for platform in platforms:
        buttons.append(InlineKeyboardButton(
            text=f'Authorize in {platform.type.name.capitalize()}',
            url=await platform.get_authorization_url(sign(user_id))
        ))

    return InlineKeyboardMarkup(inline_keyboard=chunks(buttons, 2))


@dp.message(Command('link', ignore_case=True))
async def link_command_handler(message: Message) -> None:
    assert message.from_user is not None

    await message.reply('Click on the buttons below to authorize in platforms',
                        reply_markup=await get_auth_keyboard(message.from_user.id))
