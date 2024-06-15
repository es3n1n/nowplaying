from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from spotipy import SpotifyException

from ...core.config import config
from ...core.spotify import spotify
from ...database import db
from ...util.logger import logger
from ..bot import dp
from .link import link_command_handler


async def try_controls(payload: str, message: Message) -> bool:
    uri = config.decode_start_url(payload)
    if not uri:
        return False

    if uri == 'link':
        await link_command_handler(message)
        return True

    if not uri.startswith('spotify:track:'):
        return False

    assert message.from_user is not None
    try:
        client = spotify.from_telegram_id(message.from_user.id)
        track = await client.get_track(uri)
        if not track:
            return False
    except SpotifyException as e:
        logger.opt(exception=e).error('Error')
        await message.reply('Something goofed up, contact @invlpg')
        return True

    await message.reply(
        f'{track.artist} - {track.name}\nUse the buttons bellow to control your Spotify playback.',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Play', callback_data=f'play_{uri}'),
                    InlineKeyboardButton(text='Add to queue', callback_data=f'queue_{uri}'),
                ]
            ]
        )
    )
    return True


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    assert message.from_user is not None
    assert message.text is not None

    authorized: bool = db.is_user_authorized(message.from_user.id)

    if message.text.find(' ') != -1 and authorized:
        payload = message.text.split(' ', maxsplit=1)[1]

        if await try_controls(payload, message):
            return

    msg = f'Hello, {message.from_user.full_name}'
    if authorized:
        msg += '\nYou are already authorized, check out the inline bot menu to see your recent tracks'
    else:
        msg += '\nTo continue, please link your spotify account using the /link command'

    await message.reply(msg)
