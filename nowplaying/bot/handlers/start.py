from aiogram import html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from nowplaying.bot.bot import bot, dp
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.callback_buttons import CallbackButton
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.enums.start_actions import StartAction
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.user_config import UserConfig
from nowplaying.platforms import get_platform_from_telegram_id, soundcloud, yandex
from nowplaying.util.string import QUERY_SEPARATOR, encode_query, extract_from_query

from .link import get_auth_keyboard


# Special platforms where we're hijacking the token
SPECIAL_PLATFORMS = {
    'ym_': yandex,
    'sc_': soundcloud,
}


async def send_auth_msg(telegram_id: int, platform_type: SongLinkPlatformType) -> None:
    user_config = await db.get_user_config(telegram_id)
    await bot.send_message(
        telegram_id,
        user_config.text(
            f'Successfully authorized in {html.bold(platform_type.name.title())}!'
            '\nYou can customize your experience (like download quality) in /settings.'
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=user_config.text('Open inline menu'),
                        switch_inline_query_current_chat='',
                    )
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


async def _handle_controls(uri: str, message: Message, user_config: UserConfig) -> bool:
    if message.from_user is None:
        raise ValueError

    platform_name, track_id = extract_from_query(uri, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(message.from_user.id, platform_type):
        return False

    client = await get_platform_from_telegram_id(message.from_user.id, platform_type)
    track = await client.get_track(track_id)

    if not track:
        return False

    buttons: list[InlineKeyboardButton] = []

    if client.features.get(PlatformFeature.PLAY):
        buttons.append(
            InlineKeyboardButton(
                text=user_config.text('Play'),
                callback_data=encode_query(CallbackButton.PLAY_PREFIX, uri),
            )
        )

    if client.features.get(PlatformFeature.ADD_TO_QUEUE):
        buttons.append(
            InlineKeyboardButton(
                text=user_config.text('Add to queue'),
                callback_data=encode_query(CallbackButton.ADD_TO_QUEUE_PREFIX, uri),
            )
        )

    has_likes = False
    if client.features.get(PlatformFeature.LIKE):
        has_likes = True
        buttons.append(
            InlineKeyboardButton(
                text=user_config.text('❤️'),
                callback_data=encode_query(CallbackButton.LIKE_PREFIX, uri),
            )
        )

    if not buttons:
        return False

    text: str = f'{track.artist} - {track.name}'[:128]
    text += user_config.text(
        '\n\nUse the buttons bellow to control your playback' + (' or like the track.' if has_likes else '.')
    )

    if client.media_notice:
        text += user_config.text(f'\n\n{client.media_notice}')

    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                buttons,
            ],
        ),
    )
    return True


async def _try_controls(payload: str, message: Message, user_config: UserConfig) -> bool:
    uri = config.decode_start_url(payload)
    if not uri:
        return False

    if QUERY_SEPARATOR not in uri:
        return False

    return await _handle_controls(uri, message, user_config)


async def _try_start_cmds(message: Message, *, authorized: bool, user_config: UserConfig) -> bool:
    if message.text is None or message.from_user is None:
        return False

    if message.text.find(' ') == -1:
        return False

    payload = message.text.split(' ', maxsplit=1)[1]

    # Try the special platforms where we're hijacking the token
    for key, platform in SPECIAL_PLATFORMS.items():
        if not payload.startswith(key):
            continue

        await platform.from_auth_callback(message.from_user.id, payload[len(key) :])
        await send_auth_msg(message.from_user.id, platform.type)
        return True

    if payload == StartAction.SIGN_EXPIRED.value:
        await message.reply(
            text=(
                user_config.text(
                    html.bold('This authorization url has expired.')
                    + '\n\nPlease try to authorize again using any any of the links above:'
                )
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=await get_auth_keyboard(message.from_user.id, user_config),
        )
        return True

    return authorized and await _try_controls(payload, message, user_config)


async def _start_message_authorized(user_config: UserConfig) -> str:
    me = await bot.me()
    bot_mention = '@' + str(me.username)

    msg = "Hi! Here's what you can do:"

    msg += f'\n* {html.bold("Access recent tracks")}: Type {html.code(bot_mention)} and press space in any chat.'
    msg += f'\n* {html.bold("Link more accounts")}: Use the buttons below.'

    flac_status = 'enabled' if user_config.download_flac else 'disabled'
    flac_action = 'disable it for smaller files' if user_config.download_flac else 'enable it for higher quality'
    msg += (
        f'\n* {html.bold("Adjust file quality")}: Lossless audio is currently <b>{flac_status}</b>. '
        f'Visit /settings to {flac_action}.'
    )

    return msg


def _start_message_unauthorized() -> str:
    return (
        'Hi!'
        '\nI am a bot that will help you with sending your currently-playing songs right in telegram.'
        '\n\nTo get started, please link an account from one of our supported platforms using the buttons below.'
    )


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    user_config = await db.get_user_config(message.from_user.id)
    authorized: bool = await db.is_user_authorized_globally(message.from_user.id)
    if await _try_start_cmds(message, authorized=authorized, user_config=user_config):
        return

    sections = []
    if authorized:
        sections.append(await _start_message_authorized(user_config))
    else:
        sections.append(_start_message_unauthorized())

    cached_tracks_count = await db.get_cached_files_count_for_user(message.from_user.id)
    tracks_sent = await db.get_user_sent_tracks_count(message.from_user.id)
    if authorized and (cached_tracks_count or tracks_sent):
        sections.append(
            'Your activity:'
            f'\n* Tracks cached from your requests: {html.code(str(cached_tracks_count))}'
            f'\n* Total tracks you sent: {html.code(str(tracks_sent))}'
        )

    sections.append(
        f"{html.link('News', config.NEWS_CHANNEL_URL)} / "
        f"{html.link('Source code', config.SOURCE_CODE_URL)} / "
        f"{html.link('Feedback', config.developer_url)}"
    )

    await message.reply(
        text=user_config.text('\n\n'.join(sections)),
        reply_markup=await get_auth_keyboard(message.from_user.id, user_config),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
