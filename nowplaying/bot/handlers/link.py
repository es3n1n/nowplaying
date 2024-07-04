from urllib.parse import unquote

from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.database import db
from ...core.sign import sign
from ...platforms import platforms
from ...util.string import chunks
from ..bot import dp


async def get_auth_keyboard(user_id: int) -> InlineKeyboardMarkup:
    authorized_platforms = await db.get_user_authorized_platforms(user_id)

    buttons = []
    for platform in platforms:
        is_authorized: bool = platform.type in authorized_platforms

        text = f'Authorize in {platform.type.name.capitalize()}'
        if is_authorized:
            text = f'(re){text}'

        url = await platform.get_authorization_url(sign(user_id))
        buttons.append(InlineKeyboardButton(
            text=text,
            url=unquote(url),  # goofy fix for the macOS double urlencoding issue, idek don't ask me thx
        ))

    return InlineKeyboardMarkup(inline_keyboard=chunks(buttons, 2))


@dp.message(Command('link', ignore_case=True))
async def link_command_handler(message: Message) -> None:
    if message.from_user is None:
        raise ValueError()

    await message.reply(
        'Click on the buttons below to authorize in platforms',
        reply_markup=await get_auth_keyboard(message.from_user.id),
    )
