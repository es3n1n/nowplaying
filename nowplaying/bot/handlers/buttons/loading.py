from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot
from nowplaying.bot.caching import DOWNLOADING_LOCKS
from nowplaying.bot.handlers.inline.chosen_inline_result import update_placeholder_message_audio
from nowplaying.util.string import extract_from_query


async def handle_loading_button(query: CallbackQuery) -> None:
    if not query.data or not query.inline_message_id:
        msg = 'Query data is None'
        raise ValueError(msg)

    query_args = extract_from_query(query.data, arguments_count=2)
    if len(query_args) != 2:  # noqa: PLR2004
        await bot.answer_callback_query(
            query.id,
            text='It seems like you are trying to click on a very old button.'
            '\nUnfortunately, these (old) buttons are not supported anymore.'
            '\nYou can generate a new one by sending fresh-new track from inline menu.',
            show_alert=True,
        )
        return

    _, track_uri = query_args
    if DOWNLOADING_LOCKS.is_locked(track_uri):
        await bot.answer_callback_query(query.id, text='Already downloading the audio, please wait.')
        return

    try:
        await update_placeholder_message_audio(query.from_user, track_uri, query.inline_message_id)
        await bot.answer_callback_query(query.id, text='Downloading started.')
    except ValueError:
        await bot.answer_callback_query(query.id, text='Sorry, but you can not use this button (authorize first).')
