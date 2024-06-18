from aiogram.types import CallbackQuery

from ...core.database import db
from ...models.song_link import SongLinkPlatformType
from ...platforms import get_platform_from_telegram_id
from ..bot import bot, dp


@dp.callback_query()
async def controls_handler(query: CallbackQuery) -> None:
    assert query.data is not None
    if query.data == 'loading':
        await bot.answer_callback_query(query.id, text='Downloading the audio, please wait.')
        return

    if query.data.startswith('logout_'):
        command, platform_name = query.data.split('_', maxsplit=1)
        platform_type = SongLinkPlatformType(platform_name)

        if db.delete_user_token(query.from_user.id, platform_type):
            await bot.answer_callback_query(query.id, text='Successfully logged out')
            return

        await bot.answer_callback_query(query.id, text='Unable to logout, are you sure you are authorized?')
        return

    command, platform_name, track_id = query.data.split('_', maxsplit=2)
    platform_type = SongLinkPlatformType(platform_name)

    if not db.is_user_authorized(query.from_user.id, platform_type):
        await bot.answer_callback_query(query.id, text='Please authorize first')
        return

    client = await get_platform_from_telegram_id(query.from_user.id, platform_type)

    if command == 'play':
        await client.play(track_id)
    elif command == 'queue':
        await client.add_to_queue(track_id)

    await bot.answer_callback_query(query.id, text='Done')