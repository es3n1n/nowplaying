from aiogram.exceptions import AiogramError, TelegramAPIError
from aiogram.types import BufferedInputFile, URLInputFile, User

from nowplaying.bot.bot import bot
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.models.track import Track


async def get_cached_file_id(uri: str) -> str | None:
    file_id = await db.get_cached_file(uri)
    if file_id is None:
        return None

    # Verifying that file id isn't expired
    try:
        await bot.get_file(file_id)
    except (AiogramError, TelegramAPIError):
        return None
    return file_id


async def cache_file(
    track: Track,
    file_data: bytes,
    thumbnail_url: str | None,
    user: User,
) -> str:
    # Special handling for UUIDs
    uri_safe: str = track.uri.replace('-', '_')

    thumbnail: URLInputFile | None = None
    if thumbnail_url:
        thumbnail = URLInputFile(url=thumbnail_url)

    caption: str = f'#{uri_safe}\n'
    caption += f'#uid_{user.id} #u_{user.username!s} {user.full_name}\n'
    caption += f'{track.artist} - {track.name}'

    sent = await bot.send_audio(
        config.BOT_CACHE_CHAT_ID,
        BufferedInputFile(file=file_data, filename=f'{track.artist} - {track.name}.mp3'),
        caption=caption,
        performer=track.artist,
        title=track.name,
        thumbnail=thumbnail,
    )
    if sent.audio is None:
        msg = 'Audio is none'
        raise ValueError(msg)

    await db.store_cached_file(track.uri, sent.audio.file_id)
    return sent.audio.file_id
