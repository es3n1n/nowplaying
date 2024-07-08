from aiogram import html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ...core.config import config
from ...core.database import db
from ...enums.callback_buttons import CallbackButton
from ...enums.start_actions import StartAction
from ...models.song_link import SongLinkPlatformType
from ...platforms import get_platform_from_telegram_id, yandex
from ...routes.ext import send_auth_msg
from ...util.string import QUERY_SEPARATOR, encode_query, extract_from_query
from ..bot import dp
from .link import get_auth_keyboard


async def _handle_controls(uri: str, message: Message) -> bool:
    if message.from_user is None:
        raise ValueError()

    platform_name, track_id = extract_from_query(uri, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(message.from_user.id, platform_type):
        return False

    client = await get_platform_from_telegram_id(message.from_user.id, platform_type)
    track = await client.get_track(track_id)

    if not track:
        return False

    await message.reply(
        (
            f'{track.artist} - {track.name}\n'
            + 'Use the buttons bellow to control your playback.'
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Play', callback_data=encode_query(CallbackButton.PLAY_PREFIX, uri),
                    ),
                    InlineKeyboardButton(
                        text='Add to queue', callback_data=encode_query(CallbackButton.ADD_TO_QUEUE_PREFIX, uri),
                    ),
                ],
            ],
        ),
    )
    return True


async def _try_controls(payload: str, message: Message) -> bool:
    uri = config.decode_start_url(payload)
    if not uri:
        return False

    if QUERY_SEPARATOR not in uri:
        return False

    return await _handle_controls(uri, message)


async def _try_start_cmds(message: Message, authorized: bool) -> bool:
    if message.text is None or message.from_user is None:
        return False

    if message.text.find(' ') == -1:
        return False

    payload = message.text.split(' ', maxsplit=1)[1]

    if payload.startswith('ym_'):
        await yandex.from_auth_callback(message.from_user.id, payload[3:])
        await send_auth_msg(message.from_user.id, 'yandex')
        return True

    if payload == StartAction.SIGN_EXPIRED.value:
        await message.reply(
            text=(
                html.bold('This authorization url has expired.')
                + '\n\nPlease try to authorize again using any any of the links above:'
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=await get_auth_keyboard(message.from_user.id),
        )
        return True

    return authorized and await _try_controls(payload, message)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise ValueError()

    authorized: bool = await db.is_user_authorized_globally(message.from_user.id)
    if await _try_start_cmds(message, authorized):
        return

    msg = f'Hello, {message.from_user.full_name}'
    if authorized:
        msg += '\nYou are already authorized, check out the inline bot menu to see your recent tracks'
        msg += '\nTo link a few more accounts please use the buttons below'
    else:
        msg += '\nTo link your account please use the buttons below'

    await message.reply(msg, reply_markup=await get_auth_keyboard(message.from_user.id))
