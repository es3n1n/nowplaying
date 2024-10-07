from aiogram.types import CallbackQuery

from nowplaying.bot.bot import bot
from nowplaying.core.database import db
from nowplaying.enums.callback_buttons import CallbackButton
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.enums.platform_type import SongLinkPlatformType
from nowplaying.platforms import get_platform_from_telegram_id
from nowplaying.platforms.abc import PlatformClientABC, PlatformClientSideError
from nowplaying.util.string import extract_from_query


def is_feature_supported(client: PlatformClientABC, command: str) -> bool:
    feature_map = {
        CallbackButton.PLAY_PREFIX.value: PlatformFeature.PLAY,
        CallbackButton.ADD_TO_QUEUE_PREFIX.value: PlatformFeature.ADD_TO_QUEUE,
    }
    return client.features.get(feature_map[command], False)


async def execute_command(client: PlatformClientABC, command: str, track_id: str) -> None:
    match command:
        case CallbackButton.PLAY_PREFIX.value:
            await client.play(track_id)
        case CallbackButton.ADD_TO_QUEUE_PREFIX.value:
            await client.add_to_queue(track_id)


async def _handle_media_buttons(query: CallbackQuery) -> None:
    if query.data is None:
        msg = 'Unsupported query data'
        raise ValueError(msg)

    command, platform_name, track_id = extract_from_query(query.data, arguments_count=3)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(query.from_user.id, platform_type):
        await bot.answer_callback_query(query.id, 'Please authorize first')
        return

    client = await get_platform_from_telegram_id(query.from_user.id, platform_type)

    if not is_feature_supported(client, command):
        await bot.answer_callback_query(query.id, 'Unsupported command')
        return

    await execute_command(client, command, track_id)
    await bot.answer_callback_query(query.id, 'Done')


async def handle_media_buttons(query: CallbackQuery) -> None:
    try:
        await _handle_media_buttons(query)
    except (ValueError, PlatformClientSideError) as err:
        await bot.answer_callback_query(query.id, f'Error: {err}')
