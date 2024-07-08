from aiogram.types import CallbackQuery

from ...core.database import db
from ...enums.callback_buttons import CallbackButtons
from ...models.song_link import SongLinkPlatformType
from ...platforms import get_platform_from_telegram_id
from ...util.string import extract_from_query
from ..bot import bot, dp


async def handle_logout(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError()

    command, platform_name = extract_from_query(query.data, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if await db.delete_user_token(query.from_user.id, platform_type):
        await bot.answer_callback_query(query.id, text='Successfully logged out')
        return

    await bot.answer_callback_query(query.id, text='Unable to logout, are you sure you are authorized?')


async def handle_controls(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError()

    command, platform_name, track_id = extract_from_query(query.data, arguments_count=3)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(query.from_user.id, platform_type):
        await bot.answer_callback_query(query.id, text='Please authorize first')
        return

    client = await get_platform_from_telegram_id(query.from_user.id, platform_type)

    if command == CallbackButtons.PLAY_PREFIX:
        await client.play(track_id)
    elif command == CallbackButtons.ADD_TO_QUEUE_PREFIX:
        await client.add_to_queue(track_id)

    await bot.answer_callback_query(query.id, text='Done')


@dp.callback_query()
async def controls_handler(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError()

    if query.data == CallbackButtons.LOADING:
        await bot.answer_callback_query(query.id, text='Downloading the audio, please wait.')
        return

    if query.data.startswith(CallbackButtons.LOGOUT_PREFIX):
        await handle_logout(query)
        return

    await handle_controls(query)
