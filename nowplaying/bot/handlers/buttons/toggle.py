from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot
from nowplaying.bot.handlers.settings import get_user_config_buttons
from nowplaying.core.database import db
from nowplaying.util.string import extract_from_query


async def on_changed(user_id: int, field: str, *, new_value: bool) -> None:
    if field == 'stats_opt_out' and new_value:
        await db.strip_user_id_from_cached_files(user_id)


async def handle_toggle_button(query: CallbackQuery) -> None:
    if query.data is None or query.message is None:
        raise ValueError

    _, var_name = extract_from_query(query.data, arguments_count=2)
    config = await db.get_user_config(query.from_user.id)
    if var_name not in config.model_fields:
        err_msg = f'Invalid config variable: {var_name}'
        raise ValueError(err_msg)

    new_value = not getattr(config, var_name)
    setattr(config, var_name, new_value)

    await db.update_config_var(query.from_user.id, var_name, new_value=new_value)
    await on_changed(query.from_user.id, var_name, new_value=new_value)

    await bot.answer_callback_query(query.id, text=f'Toggled to {new_value}')

    buttons = await get_user_config_buttons(query.from_user.id, config)
    try:
        await bot.edit_message_reply_markup(
            chat_id=query.from_user.id,
            message_id=query.message.message_id,
            reply_markup=buttons,
        )
    except TelegramBadRequest as err:
        if 'message is not modified' not in str(err):
            raise
