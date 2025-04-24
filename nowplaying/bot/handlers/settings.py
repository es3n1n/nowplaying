from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from nowplaying.bot.bot import dp
from nowplaying.core.database import db
from nowplaying.enums.callback_buttons import CallbackButton
from nowplaying.models.user_config import UserConfig
from nowplaying.util.string import encode_query


SETTINGS_TEXT = (
    'Click on the buttons below to toggle values'
    '\n\nWhen opting out from statistics, all the stored stats data will be deleted'
)


async def get_user_config_buttons(user_id: int, config: UserConfig | None = None) -> InlineKeyboardMarkup:
    if not config:
        config = await db.get_user_config(user_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=config.text(f'{attribute.description}: {getattr(config, name)}'),
                    callback_data=encode_query(CallbackButton.CONFIG_TOGGLE_PREFIX, name),
                )
            ]
            for name, attribute in config.model_fields.items()
        ]
    )


@dp.message(Command('settings', 'config', ignore_case=True))
async def config_command_handler(message: Message) -> None:
    if message.from_user is None:
        raise ValueError

    config = await db.get_user_config(message.from_user.id)
    await message.reply(
        config.text(SETTINGS_TEXT),
        reply_markup=await get_user_config_buttons(message.from_user.id, config),
    )
