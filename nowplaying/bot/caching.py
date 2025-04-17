from aiogram.exceptions import AiogramError, TelegramAPIError, TelegramEntityTooLarge
from aiogram.types import BufferedInputFile, Message, URLInputFile, User

from nowplaying.bot.bot import bot
from nowplaying.bot.reporter import report_error
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.models.track import Track
from nowplaying.util.asyncio import LockManager
from nowplaying.util.retries import retry


# key is uri
DOWNLOADING_LOCKS = LockManager()


class CachingFileTooLargeError(Exception):
    """File is too large to cache."""


async def get_cached_file_id(uri: str) -> str | None:
    file_id = await db.get_cached_file(uri)
    if file_id is None:
        return None

    # Verifying that file id isn't expired
    try:
        await bot.get_file(file_id)
    except (AiogramError, TelegramAPIError) as err:
        if not any(x in str(err).lower() for x in ('file is too big',)):
            return None
    return file_id


async def cache_file(
    track: Track,
    file_data: bytes,
    file_extension: str,
    thumbnail_url: str | None,
    user: User,
    duration_seconds: int,
) -> str:
    # Special handling for UUIDs
    uri_safe = track.uri.replace('-', '_')

    thumbnail: URLInputFile | None = None
    if thumbnail_url:
        thumbnail = URLInputFile(url=thumbnail_url)

    caption = f'#{uri_safe}\n'
    caption += f'#uid_{user.id} #u_{user.username!s} {user.full_name}'
    caption = caption[:100]

    file_name = f'{track.artist} - {track.name}'
    # Telegram API automatically converts ogg files to voice messages;
    #   however, they are checking this by mime_type.
    # Ogg has multiple mime types, so in our "patched" bot api instances,
    #   .vorbis files will be sent as .ogg with `audio/vorbis` mime_type instead of `audio/ogg`.
    # No, this is not a behavior specific to bot api, even if you set the voice_note
    #   within file attrs to False, it will still be sent as a voice message through raw MTProto.
    file_name += f'.{file_extension if file_extension != "ogg" else "vorbis"}'

    sent: Message | None = None

    async for _ in retry(3):
        try:
            sent = await bot.send_audio(
                config.BOT_CACHE_CHAT_ID,
                BufferedInputFile(file=file_data, filename=file_name),
                caption=caption,
                performer=track.artist,
                title=track.name,
                thumbnail=thumbnail,
                duration=duration_seconds or None,  # in case for some reason, api returned 0
                request_timeout=config.BOT_UPLOAD_FILE_TIMEOUT,
            )
        except TelegramEntityTooLarge as exc:
            raise CachingFileTooLargeError from exc
        except TelegramAPIError as exc:
            # Report the error and try again
            await report_error(f'Unable to cache file for {track.uri}\n{caption!r}', exc)
            continue

        break

    if not sent or not sent.audio:
        msg = 'Audio is none'
        raise ValueError(msg)

    await db.store_cached_file(track.uri, sent.audio.file_id)
    return sent.audio.file_id
