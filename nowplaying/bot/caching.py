from io import BytesIO

from aiogram.exceptions import AiogramError, TelegramAPIError
from aiogram.types import BufferedInputFile, User

from ..core.config import config
from ..database import db
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


async def cache_file(uri: str, data: BytesIO, performer: str, name: str, full_title: str, user: User) -> str:
    sent = await bot.send_audio(
        config.BOT_CACHE_CHAT_ID,
        BufferedInputFile(file=data.read(), filename=f'{full_title}.mp3'),
        caption=f'{uri} #id{user.id} {full_title}',
        performer=performer,
        title=name,
    )
    assert sent.audio is not None

    db.store_cached_file(uri, sent.audio.file_id)
    return sent.audio.file_id
