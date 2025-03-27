from telethon import TelegramClient, types
from pathlib import Path
from nowplaying.core.config import config
from nowplaying.util.logger import logger
from nowplaying.core.database import db

root_dir = Path(__file__).parent
client = TelegramClient(
    session=root_dir / 'cache_migration' / 'session.session',
    api_id=config.TELEGRAM_API_ID,
    api_hash=config.TELEGRAM_API_HASH,
    device_model='1.0.0',
    system_version='1.3.3.7',
    app_version='1.0.0',
    lang_code='en',
    system_lang_code='en',
)


async def main() -> None:
    await db.init()

    # uri, message_id
    to_purge: list[tuple[str, int]] = []

    logger.info('Fetching cached tracks')
    async for msg in client.iter_messages(entity=config.BOT_CACHE_CHAT_ID):
        if not isinstance(msg, types.Message):
            continue

        # Skip non-audio messages
        if not msg.media or not isinstance(msg.media, types.MessageMediaDocument):
            continue

        audio: types.Document | None = getattr(msg, 'audio', None)
        if not audio:
            continue

        duration: int | None = None
        for attribute in audio.attributes:
            if not isinstance(attribute, types.DocumentAttributeAudio):
                continue

            duration = attribute.duration
            break

        # Remove only with duration <= 0 or None
        if duration is not None and duration > 0:
            continue

        to_purge.append((msg.message.split()[0].lstrip('#'), msg.id))

    logger.info(f'Found {len(to_purge)} tracks to purge')
    for i in range(0, len(to_purge), 100):
        uris = []
        message_ids = []
        for uri, message_id in to_purge[i : i + 100]:
            uris.append(uri)
            message_ids.append(message_id)

        logger.info(f'Processing {i} to {i + 100}')
        await db.delete_cached_files(uris)
        await client.delete_messages(config.BOT_CACHE_CHAT_ID, message_ids=message_ids)


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
