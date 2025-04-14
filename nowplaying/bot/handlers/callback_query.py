from aiogram.types import CallbackQuery

from nowplaying.bot.bot import dp
from nowplaying.bot.handlers.buttons.loading import handle_loading_button
from nowplaying.bot.handlers.buttons.logout import handle_logout_button
from nowplaying.bot.handlers.buttons.media import handle_media_buttons
from nowplaying.enums.callback_buttons import CallbackButton


@dp.callback_query()
async def controls_handler(query: CallbackQuery) -> None:
    if query.data is None:
        raise ValueError

    if query.data.startswith(CallbackButton.LOADING):
        await handle_loading_button(query)
        return

    if query.data.startswith(CallbackButton.LOGOUT_PREFIX):
        await handle_logout_button(query)
        return

    await handle_media_buttons(query)
