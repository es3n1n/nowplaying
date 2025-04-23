from aiogram.enums import ParseMode
from aiogram.types import ChosenInlineResult, User

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.caching import (
    DOWNLOADING_LOCKS,
    CachingFileTooLargeError,
    cache_file,
    get_cached_file_ensured,
)
from nowplaying.bot.reporter import report_error
from nowplaying.core.database import db
from nowplaying.external.udownloader import UdownloaderError, download
from nowplaying.models.cached_file import CachedFile
from nowplaying.models.track import Track
from nowplaying.models.user_config import UserConfig
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


async def _get_cached_file(
    inline_message_id: str, from_user: User, track: Track, caption: str, user_config: UserConfig
) -> CachedFile | None:
    # Increment sent tracks statistics
    if not user_config.stats_opt_out:
        await db.increment_sent_tracks_count(from_user.id)

    # Cached file, no need to download
    cached_file = await get_cached_file_ensured(track.uri)
    if cached_file:
        return cached_file

    # Cache missed, downloading
    try:
        downloaded = await download(await track.song_link())  # type: ignore[arg-type]
    except UdownloaderError as err:
        await _unavailable(caption, str(err), inline_message_id)
        await report_error(f'Unable to download {track.model_dump_json()}', exception=err)
        return None

    try:
        return await cache_file(
            track=track,
            file=downloaded,
            user=from_user,
            user_config=user_config,
        )
    except CachingFileTooLargeError:
        # TODO(es3n1n): we should remember that this file is too large and not try to cache it again
        await _unavailable(caption, 'File is too large to cache', inline_message_id)  # type: ignore[arg-type]
        await report_error(f'Unable to download {track.model_dump_json()}\nError = file is too large to cache')
        return None


async def get_cached_file(
    inline_message_id: str, from_user: User, track: Track, caption: str, user_config: UserConfig
) -> CachedFile | None:
    async with DOWNLOADING_LOCKS.lock(track.uri):
        return await _get_cached_file(inline_message_id, from_user, track, caption, user_config)


async def update_placeholder_message_audio(from_user: User, uri: str, inline_message_id: str) -> None:
    client, track = await parse_track_from_uri(from_user.id, uri)
    if track is None or client is None or not await track.song_link():
        # :shrug:, there's nothing we can do
        logger.error(from_user.model_dump())
        logger.error(f'client: {client} | track: {track} | song_link: {await track.song_link()}')
        await report_error('Something unusual happened, track or client or song link is None')
        return

    user_config = await db.get_user_config(from_user.id)
    caption = await track_to_caption(user_config, client, track, quality=None, is_getter_available=True)
    logger.info(
        f'Processing {track.artist} - {track.name} ({track.platform.name})',
    )

    file = await get_cached_file(inline_message_id, from_user, track, caption, user_config)
    if not file:
        return

    await update_inline_message_audio(
        track=track,
        cached_file=file,
        inline_message_id=inline_message_id,
        user_config=user_config,
        client=client,
    )


@dp.chosen_inline_result()
async def chosen_inline_result_handler(inline_result: ChosenInlineResult) -> None:
    if inline_result.inline_message_id is None:
        return

    await update_placeholder_message_audio(
        inline_result.from_user, inline_result.result_id, inline_result.inline_message_id
    )
