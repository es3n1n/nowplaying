from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.handlers.buttons.logout import handle_logout_button
from nowplaying.bot.handlers.buttons.media import handle_media_buttons
from nowplaying.enums.callback_buttons import CallbackButton


@dp.callback_query()
async def controls_handler(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError

    if query.data == CallbackButton.LOADING:
        await bot.answer_callback_query(query.id, text='Downloading the audio, please wait.')
        return

    if query.data.startswith(CallbackButton.LOGOUT_PREFIX):
        await handle_logout_button(query)
        return

    await handle_media_buttons(query)
