from aiogram.enums import ParseMode
from aiogram.types import ChosenInlineResult

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.caching import CachingFileTooLargeError
from nowplaying.bot.reporter import report_error
from nowplaying.external.udownloader import download_mp3
from nowplaying.util.logger import logger

from .inline import parse_inline_result_query
from .inline_utils import UNAVAILABLE_MSG_DETAILED, cache_audio_and_edit, track_to_caption


async def _unavailable(caption: str, error: str, inline_message_id: str) -> None:
    caption = f'{UNAVAILABLE_MSG_DETAILED.format(error=str(error))}\n{caption}'
    await bot.edit_message_caption(
        inline_message_id=inline_message_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )


@dp.chosen_inline_result()
async def chosen_inline_result_handler(inline_result: ChosenInlineResult) -> None:
    if inline_result.inline_message_id is None:
        return

    client, track = await parse_inline_result_query(inline_result)
    if track is None or client is None or not track.song_link:
        # :shrug:, there's nothing we can do
        logger.error(inline_result.model_dump())
        logger.error(f'client: {client} | track: {track}')
        await report_error('Something unusual happened, track or client is None')
        return

    caption = track_to_caption(client, track, is_getter_available=True)
    logger.info(
        f'Downloading {track.artist} - {track.name} ({track.platform.name})',
    )

    downloaded = await download_mp3(track.song_link)
    if downloaded.error or not downloaded.mp3_data or downloaded.duration_sec is None:
        await _unavailable(caption, downloaded.error or 'Unknown error', inline_result.inline_message_id)
        await report_error(f'Unable to download {track.model_dump_json()}\nError = {downloaded.error}')
        return

    try:
        await cache_audio_and_edit(
            track=track,
            mp3=downloaded.mp3_data,
            thumbnail=downloaded.thumbnail_url,
            inline_result=inline_result,
            caption=caption,
            duration_seconds=downloaded.duration_sec,
        )
    except CachingFileTooLargeError:
        # TODO(es3n1n): we should remember that this file is too large and not try to cache it again
        await _unavailable(caption, 'File is too large to cache', inline_result.inline_message_id)
        await report_error(f'Unable to download {track.model_dump_json()}\nError = file is too large to cache')
        return
