from aiogram.enums import ParseMode
from aiogram.types import ChosenInlineResult, User

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.caching import DOWNLOADING_LOCKS, CachingFileTooLargeError, cache_file, get_cached_file_id
from nowplaying.bot.reporter import report_error
from nowplaying.external.udownloader import download
from nowplaying.models.track import Track
from nowplaying.util.logger import logger

from .inline import parse_track_from_uri
from .inline_utils import UNAVAILABLE_MSG_DETAILED, track_to_caption, update_inline_message_audio


async def _unavailable(caption: str, error: str, inline_message_id: str) -> None:
    caption = f'{UNAVAILABLE_MSG_DETAILED.format(error=str(error))}\n{caption}'
    await bot.edit_message_caption(
        inline_message_id=inline_message_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )


async def _get_track_file_id(inline_message_id: str, from_user: User, track: Track, caption: str) -> str | None:
    # Cached file, no need to download
    cached_file_id = await get_cached_file_id(track.uri)
    if cached_file_id:
        return cached_file_id

    # Cache missed, downloading
    downloaded = await download(await track.song_link())  # type: ignore[arg-type]
    if downloaded.error or not downloaded.data or downloaded.duration_sec is None or downloaded.file_extension is None:
        await _unavailable(caption, downloaded.error or 'Unknown error', inline_message_id)  # type: ignore[arg-type]
        await report_error(f'Unable to download {track.model_dump_json()}\nError = {downloaded.error}')
        return None

    try:
        return await cache_file(
            track=track,
            file_data=downloaded.data,
            file_extension=downloaded.file_extension,
            thumbnail_url=downloaded.thumbnail_url,
            user=from_user,
            duration_seconds=downloaded.duration_sec,
        )
    except CachingFileTooLargeError:
        # TODO(es3n1n): we should remember that this file is too large and not try to cache it again
        await _unavailable(caption, 'File is too large to cache', inline_message_id)  # type: ignore[arg-type]
        await report_error(f'Unable to download {track.model_dump_json()}\nError = file is too large to cache')
        return None


async def get_track_file_id(inline_message_id: str, from_user: User, track: Track, caption: str) -> str | None:
    async with DOWNLOADING_LOCKS.lock(track.uri):
        return await _get_track_file_id(inline_message_id, from_user, track, caption)


async def update_placeholder_message_audio(from_user: User, uri: str, inline_message_id: str) -> None:
    client, track = await parse_track_from_uri(from_user.id, uri)
    if track is None or client is None or not await track.song_link():
        # :shrug:, there's nothing we can do
        logger.error(from_user.model_dump())
        logger.error(f'client: {client} | track: {track}')
        await report_error('Something unusual happened, track or client is None')
        return

    caption = await track_to_caption(client, track, is_getter_available=True)
    logger.info(
        f'Processing {track.artist} - {track.name} ({track.platform.name})',
    )

    file_id = await get_track_file_id(inline_message_id, from_user, track, caption)
    if not file_id:
        return

    await update_inline_message_audio(
        track=track,
        file_id=file_id,
        caption=caption,
        inline_message_id=inline_message_id,
    )


@dp.chosen_inline_result()
async def chosen_inline_result_handler(inline_result: ChosenInlineResult) -> None:
    if inline_result.inline_message_id is None:
        return

    await update_placeholder_message_audio(
        inline_result.from_user, inline_result.result_id, inline_result.inline_message_id
    )
