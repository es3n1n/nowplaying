from io import BytesIO

from aiogram.exceptions import AiogramError, TelegramAPIError
from aiogram.types import BufferedInputFile, URLInputFile, User

from ..core.config import config
from ..core.database import db
from .bot import bot


async def get_cached_file_id(uri: str) -> str | None:
    file_id = db.get_cached_file(uri)
    if file_id is None:
        return None

    # Verifying that file id isn't expired
    try:
        await bot.get_file(file_id)
    except (AiogramError, TelegramAPIError):
        return None
    return file_id


async def cache_file(
        uri: str,
        data: BytesIO,
        thumbnail_url: str,
        performer: str,
        name: str,
        user: User
) -> str:
    sent = await bot.send_audio(
        config.BOT_CACHE_CHAT_ID,
        BufferedInputFile(file=data.read(), filename=f'{performer} - {name}.mp3'),
        caption=f'#{uri.replace("-", "_")}\n'
                f'#uid_{user.id} #u_{str(user.username)} {user.full_name}\n'
                f'{performer} - {name}',
        performer=performer,
        title=name,
        thumbnail=URLInputFile(url=thumbnail_url) if thumbnail_url != '' else None,
    )
    assert sent.audio is not None

    db.store_cached_file(uri, sent.audio.file_id)
    return sent.audio.file_id
