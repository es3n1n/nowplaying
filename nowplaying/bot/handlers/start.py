from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.config import config
from ...core.database import db
from ...models.song_link import SongLinkPlatformType
from ...platforms import get_platform_from_telegram_id, yandex
from ...routes.ext import send_auth_msg
from ..bot import dp
from .link import get_auth_keyboard, link_command_handler


async def handle_controls(uri: str, message: Message) -> bool:
    if message.from_user is None:
        raise ValueError()

    platform_name, track_id = uri.split('_')
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(message.from_user.id, platform_type):
        return False

    client = await get_platform_from_telegram_id(message.from_user.id, platform_type)
    track = await client.get_track(track_id)

    if not track:
        return False

    await message.reply(
        f'{track.artist} - {track.name}\nUse the buttons bellow to control your playback.',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Play', callback_data=f'play_{uri}'),
                    InlineKeyboardButton(text='Add to queue', callback_data=f'queue_{uri}'),
                ],
            ],
        ),
    )
    return True


async def try_controls(payload: str, message: Message) -> bool:
    uri = config.decode_start_url(payload)
    if not uri:
        return False

    if uri == 'link':
        await link_command_handler(message)
        return True

    if '_' not in uri:
        return False

    return await handle_controls(uri, message)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise ValueError()

    authorized: bool = await db.is_user_authorized_globally(message.from_user.id)

    if message.text.find(' ') != -1:
        payload = message.text.split(' ', maxsplit=1)[1]

        if payload.startswith('ym_'):
            token = payload[3:]
            await yandex.from_auth_callback(message.from_user.id, token)
            await send_auth_msg(message.from_user.id, 'yandex')
            return

        if authorized and await try_controls(payload, message):
            return

    msg = f'Hello, {message.from_user.full_name}'
    if authorized:
        msg += '\nYou are already authorized, check out the inline bot menu to see your recent tracks'
        msg += '\nTo link a few more accounts please use the buttons below'
    else:
        msg += '\nTo link your account please use the buttons below'

    await message.reply(msg, reply_markup=await get_auth_keyboard(message.from_user.id))
