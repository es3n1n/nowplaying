from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot
from nowplaying.bot.caching import DOWNLOADING_LOCKS
from nowplaying.bot.handlers.inline.chosen_inline_result import update_placeholder_message_audio
from nowplaying.util.string import extract_from_query


async def handle_loading_button(query: CallbackQuery) -> None:
    if not query.data or not query.inline_message_id:
        msg = 'Query data is None'
        raise ValueError(msg)

    _, user_id, track_uri = extract_from_query(query.data, arguments_count=3)
    if not user_id.lstrip('-').isdigit() or int(user_id) != query.from_user.id:
        await bot.answer_callback_query(query.id, text='Only the sender can use this button.')
        return

    if DOWNLOADING_LOCKS.is_locked(track_uri):
        await bot.answer_callback_query(query.id, text='Already downloading the audio, please wait.')
        return

    await bot.answer_callback_query(query.id, text='Downloading started.')
    await update_placeholder_message_audio(query.from_user, track_uri, query.inline_message_id)
