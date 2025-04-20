from io import BytesIO

from aiogram.exceptions import AiogramError, TelegramAPIError, TelegramEntityTooLarge
from aiogram.types import BufferedInputFile, Message, User
from aiohttp import ClientSession

from nowplaying.bot.bot import bot
from nowplaying.bot.reporter import report_error
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.external.udownloader import DownloadedSong
from nowplaying.models.cached_file import CachedFile
from nowplaying.models.track import Track
from nowplaying.models.user_config import UserConfig
from nowplaying.util.asyncio import LockManager
from nowplaying.util.compressing import compress_jpeg
from nowplaying.util.http import STATUS_OK
from nowplaying.util.retries import retry


# key is uri
DOWNLOADING_LOCKS = LockManager()


class CachingFileTooLargeError(Exception):
    """File is too large to cache."""


async def get_cached_file_ensured(uri: str) -> CachedFile | None:
    file = await db.get_cached_file(uri)
    if file is None:
        return None

    # Verifying that file id isn't expired
    try:
        await bot.get_file(file.file_id)
    except (AiogramError, TelegramAPIError) as err:
        if not any(x in str(err).lower() for x in ('file is too big',)):
            return None
    return file


async def process_thumbnail_jpeg(thumbnail_url: str | None) -> BufferedInputFile | None:
    thumbnail: BufferedInputFile | None = None
    if not thumbnail_url:
        return thumbnail

    async with ClientSession() as session, session.get(thumbnail_url) as resp:
        if resp.status != STATUS_OK:
            msg = f'Unable to get thumbnail {resp.status}'
            raise ValueError(msg)

        data = await resp.read()
        return BufferedInputFile(
            # Compress JPEG to avoid hitting the 200 kb limit
            file=compress_jpeg(BytesIO(data), target_size_kb=200).getvalue(),
            filename='thumbnail.jpeg',
        )


async def cache_file(
    track: Track,
    file: DownloadedSong,
    user: User,
    user_config: UserConfig | None,
) -> CachedFile:
    # Special handling for UUIDs
    uri_safe = track.uri.replace('-', '_')

    stats_user_id: int | None = user.id
    stats_user_username: str | None = user.username
    stats_user_name: str | None = user.full_name

    # Set user id to None if user has opted out from stats
    if not user_config:
        user_config = await db.get_user_config(user.id)
    if user_config.stats_opt_out:
        stats_user_id = None
        stats_user_username = None
        stats_user_name = None

    # These two are important
    caption = f'#{uri_safe}'
    caption += f'\n#uid_{stats_user_id} '
    # These are not, so we can cut some parts of them
    caption += f'#u_{stats_user_username!s} {stats_user_name}'[:100]
    # Do not cut this though
    caption += (
        f'\n#bit_{file.quality["bit_depth"]} '
        f'#kbps_{file.quality["bitrate_kbps"]} '
        f'#khz_{file.quality["sample_rate_khz"]} '
        f'#p_{file.platform_name}'
    )

    file_name = f'{track.artist} - {track.name}'
    # Telegram API automatically converts ogg files to voice messages;
    #   however, they are checking this by mime_type.
    # Ogg has multiple mime types, so in our "patched" bot api instances,
    #   .vorbis files will be sent as .ogg with `audio/vorbis` mime_type instead of `audio/ogg`.
    # No, this is not a behavior specific to bot api, even if you set the voice_note
    #   within file attrs to False, it will still be sent as a voice message through raw MTProto.
    file_name += f'.{file.file_extension if file.file_extension != "ogg" else "vorbis"}'

    sent: Message | None = None
    async for _ in retry(3):
        try:
            sent = await bot.send_audio(
                config.BOT_CACHE_CHAT_ID,
                BufferedInputFile(file=file.data, filename=file_name),
                caption=caption,
                performer=track.artist,
                title=track.name,
                thumbnail=await process_thumbnail_jpeg(file.thumbnail_url),
                duration=file.duration_sec or None,  # in case for some reason, api returned 0
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

    await db.store_cached_file(track.uri, sent.audio.file_id, stats_user_id, file.quality)
    return CachedFile(file_id=sent.audio.file_id, cached_by_user_id=user.id, quality_info=file.quality)
