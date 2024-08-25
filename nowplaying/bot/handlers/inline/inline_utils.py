from typing import cast

from aiogram import html, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from nowplaying.bot.bot import bot
from nowplaying.bot.caching import cache_file
from nowplaying.core.config import config
from nowplaying.models.track import Track
from nowplaying.platforms import PlatformClientABC
from nowplaying.util.retries import retry


# Only 2 because for some slow platforms like lastfm it takes so much time to gather all the info
# This number also doesn't include the currently playing song
NUM_OF_ITEMS_TO_QUERY: int = 2
UNAVAILABLE_MSG: str = 'Error: this track is not available :('
UNAVAILABLE_MSG_DETAILED: str = 'Unavailable: {error}'


def track_to_caption(
    client: PlatformClientABC,
    track: Track,
    *,
    is_getter_available: bool = True,
    is_track_available: bool = True,
) -> str:
    play_url = config.get_start_url(track.uri)

    message_text = ''

    if not is_getter_available:
        message_text += f'Error: downloading from {track.platform.value.capitalize()} is unsupported\n'
    elif not is_track_available:
        message_text += UNAVAILABLE_MSG + '\n'

    message_text += f'{html.link(track.platform.name.capitalize(), track.url)}'

    if client.can_control_playback:
        message_text += f' ({html.link("▶️", play_url)})'

    if track.song_link is not None:
        message_text += f' | {html.link("Other", track.song_link)}'

    return message_text


async def _update_inline_message_audio(
    *,
    track: Track,
    file_id: str,
    caption: str,
    inline_message_id: str,
) -> None:
    # We are trying to lose a race with telegram's cache here, because sometimes we're too fast
    async for _ in retry(5):
        try:
            await bot.edit_message_media(
                media=types.InputMediaAudio(
                    performer=track.artist,
                    title=track.name,
                    media=file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                ),
                inline_message_id=inline_message_id,
            )
        except TelegramBadRequest as exc:
            # We just won the race
            if exc.message == 'Bad Request: MEDIA_EMPTY':
                continue

            # The message was deleted, no need to edit anything
            if exc.message == 'Bad Request: MESSAGE_ID_INVALID':
                break

            raise

        break  # Edited successfully


async def cache_audio_and_edit(
    *,
    track: Track,
    mp3: bytes,
    thumbnail: str | None,
    inline_result: types.ChosenInlineResult,
    caption: str,
) -> None:
    file_id = await cache_file(
        track=track,
        file_data=mp3,
        thumbnail_url=thumbnail,
        user=inline_result.from_user,
    )

    await _update_inline_message_audio(
        track=track,
        file_id=file_id,
        caption=caption,
        inline_message_id=cast(str, inline_result.inline_message_id),
    )
