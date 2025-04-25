from aiogram import html, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from nowplaying.bot.bot import bot
from nowplaying.core.config import config
from nowplaying.external.udownloader import SongQualityInfo
from nowplaying.models.cached_file import CachedFile
from nowplaying.models.track import Track
from nowplaying.models.user_config import UserConfig
from nowplaying.platforms import PlatformClientABC
from nowplaying.util.retries import retry


# Only 2 because for some slow platforms like lastfm it takes so much time to gather all the info
# This number also doesn't include the currently playing song
NUM_OF_ITEMS_TO_QUERY: int = 2
UNAVAILABLE_MSG: str = 'Error: this track is not available :('
UNAVAILABLE_MSG_DETAILED: str = 'Unavailable: {error}'


async def track_to_caption(
    user_config: UserConfig,
    client: PlatformClientABC,
    track: Track,
    quality: SongQualityInfo | None,
    *,
    is_getter_available: bool = True,
    is_track_available: bool = True,
) -> str:
    message_text = ''

    if not is_getter_available:
        message_text += f'Error: downloading from {track.platform.value.capitalize()} is unsupported\n'
    elif not is_track_available:
        message_text += UNAVAILABLE_MSG + '\n'

    components = [
        f'{html.link(user_config.text(track.platform.name.capitalize()), track.url)}',
    ]

    if client.can_control_playback and user_config.add_media_button:
        components[0] += f' {html.link("(▶️)", config.get_start_url(track.uri))}'

    song_link = await track.song_link()
    if user_config.add_song_link and song_link:
        components.append(f'{html.link(user_config.text("Other"), song_link)}')

    if user_config.add_bitrate and quality:
        components.append(user_config.text(f'{html.bold(str(quality["bitrate_kbps"]))} kbps'))

    if user_config.add_sample_rate and quality:
        components.append(user_config.text(f'{html.bold(str(quality["sample_rate_khz"]))} kHz'))

    message_text += ' | '.join(components)
    return message_text


async def update_inline_message_audio(
    *,
    track: Track,
    cached_file: CachedFile,
    inline_message_id: str,
    user_config: UserConfig,
    client: PlatformClientABC,
) -> None:
    # We are trying to lose a race with telegram's cache here, because sometimes we're too fast
    async for _ in retry(5):
        try:
            await bot.edit_message_media(
                media=types.InputMediaAudio(
                    performer=track.artist,
                    title=track.name,
                    media=cached_file.file_id,
                    caption=await track_to_caption(user_config, client, track, cached_file.quality_info),
                    parse_mode=ParseMode.HTML,
                ),
                inline_message_id=inline_message_id,
            )
        except TelegramBadRequest as exc:
            # We just lost the race
            if exc.message == 'Bad Request: MEDIA_EMPTY':
                continue

            # The message was deleted, no need to edit anything
            if exc.message == 'Bad Request: MESSAGE_ID_INVALID':
                break

            # A race between two uploading handlers.
            # Even though there are mutexes to synchronize, because of the nature of how telegram bot api is working,
            # there still is a chance that this might happen.
            # Worry not, though; it would not upload the same file twice, this only happens for an edit.
            if exc.message.startswith(
                'Bad Request: message is not modified: specified new '
                'message content and reply markup are exactly the same'
            ):
                break

            raise

        break  # Edited successfully
