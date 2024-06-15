from aiogram.types import CallbackQuery

from ...core.spotify import spotify
from ...database import db
from ..bot import bot, dp


@dp.callback_query()
async def controls_handler(query: CallbackQuery) -> None:
    assert query.data is not None
    if query.data == 'loading':
        await bot.answer_callback_query(query.id, text='Downloading the audio, please wait.')
        return

    if not db.is_user_authorized(query.from_user.id):
        await bot.answer_callback_query(query.id, text='Please authenticate first')
        return

    command, uri = query.data.split('_', maxsplit=1)
    client = spotify.from_telegram_id(query.from_user.id)

    if command == 'play':
        client.play(uri)
    elif command == 'queue':
        client.add_to_queue(uri)

    await bot.answer_callback_query(query.id, text='Done')
