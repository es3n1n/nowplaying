from aiogram.types import ChosenInlineResult

from ....downloaders import download_mp3
from ...bot import bot, dp
from .inline import parse_inline_result_query
from .inline_utils import UNAVAILABLE_MSG, cache_audio_and_edit, track_to_caption


@dp.chosen_inline_result()
async def chosen_inline_result_handler(inline_result: ChosenInlineResult) -> None:
    # todo @es3n1n: multiprocess queue
    if inline_result.inline_message_id is None:
        return

    client, track = await parse_inline_result_query(inline_result)
    if track is None or client is None:
        # :shrug:, there's nothing we can do
        return

    caption = track_to_caption(client, track, is_getter_available=True)
    thumbnail, mp3 = await download_mp3(track)

    if mp3 is None:
        caption = f'{UNAVAILABLE_MSG}\n{caption}'
        await bot.edit_message_caption(
            inline_message_id=inline_result.inline_message_id,
            caption=caption,
            parse_mode='HTML',
        )
        return

    await cache_audio_and_edit(
        track=track,
        mp3=mp3,
        thumbnail=thumbnail,
        user=inline_result.from_user,
        caption=caption,
        inline_message_id=inline_result.inline_message_id,
    )