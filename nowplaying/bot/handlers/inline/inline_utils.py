from io import BytesIO

from aiogram import html, types
from aiogram.enums import ParseMode

from ....core.config import config
from ....models.track import Track
from ....platforms import PlatformClientABC
from ...bot import bot
from ...caching import cache_file


# Only 2 because for some fxxcked up platforms like lastfm it takes so much time to gather all the info
# This number also doesn't include the currently playing song
NUM_OF_ITEMS_TO_QUERY: int = 2
UNAVAILABLE_MSG: str = 'Error: this track is not available :('


def track_to_caption(
    client: PlatformClientABC,
    track: Track,
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


async def cache_audio_and_edit(
    *,
    track: Track,
    mp3: BytesIO,
    thumbnail: str,
    user: types.User,
    caption: str,
    inline_message_id: str,
) -> None:
    file_id = await cache_file(
        uri=track.uri,
        file_data=mp3,
        thumbnail_url=thumbnail,
        performer=track.artist,
        name=track.name,
        user=user,
    )
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
