from collections import defaultdict

from telethon import TelegramClient, types
from pathlib import Path
from nowplaying.core.config import config
from nowplaying.util.logger import logger

root_dir = Path(__file__).parent
client = TelegramClient(
    session=root_dir / 'session.session',
    api_id=config.TELEGRAM_API_ID,
    api_hash=config.TELEGRAM_API_HASH,
    device_model='1.0.0',
    system_version='1.3.3.7',
    app_version='1.0.0',
    lang_code='en',
    system_lang_code='en',
)


async def main() -> None:
    # key is track uri
    cached_tracks: defaultdict[str, list[types.Message]] = defaultdict(list)

    logger.info('Fetching cached tracks')
    async for msg in client.iter_messages(entity=config.BOT_CACHE_CHAT_ID):
        if not isinstance(msg, types.Message):
            continue

        # Skip non-audio messages
        if not msg.media or not isinstance(msg.media, types.MessageMediaDocument):
            continue

        uri = msg.message.split()[0].lstrip('#')
        cached_tracks[uri].append(msg)

    logger.info(f'Found {len(cached_tracks)} cached tracks. Deleting duplicates')

    to_forward: list[int] = []
    for uri, track_messages in cached_tracks.items():
        # Getting rid of all duplicates
        if len(track_messages) > 1:
            await client.delete_messages(config.BOT_CACHE_CHAT_ID, message_ids=[msg.id for msg in track_messages[:-1]])
            logger.info(f'Deleted {len(track_messages) - 1} duplicates of {uri}')

        # Forward the last message to the main bot
        to_forward.append(track_messages[-1].id)

    # Forward all the messages
    logger.info(f'Forwarding {len(to_forward)} messages')
    for i in range(0, len(to_forward), 100):
        logger.info(f'Forwarding {i} to {i + 100}')
        await client.forward_messages(
            config.BOT_URL.split('/')[-1], to_forward[i : i + 100], from_peer=config.BOT_CACHE_CHAT_ID
        )


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
