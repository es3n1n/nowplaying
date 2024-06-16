from urllib.parse import quote

from aiogram.types import (
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InlineQueryResultCachedAudio,
    InputMediaAudio,
    InputTextMessageContent,
)

from ...core.config import config
from ...core.database import db
from ...downloaders import download_mp3
from ...models.song_link import SongLinkPlatformType
from ...models.track import Track
from ...platforms import PlatformClientABC, get_platform_from_telegram_id, platforms
from ...util.logger import logger
from ..bot import bot, dp
from ..caching import cache_file, get_cached_file_id


# Only 2 because for some fxxcked up platforms like lastfm it takes so much time to gather all the info
NUM_OF_ITEMS_TO_QUERY: int = 2


def url(text: str, href: str) -> str:
    return f'<a href="{href}">{text}</a>'


def track_to_caption(client: PlatformClientABC, track: Track) -> str:
    play_url = config.get_start_url(track.uri)

    message_text = ''

    if not client.features.get('track_getters', True):
        message_text += f'Error: downloading from {track.platform.value.capitalize()} is unsupported\n'

    message_text += f'{url(track.platform.value.capitalize(), track.url)}'

    if client.can_control_playback:
        message_text += f' ({url("▶️", play_url)})'

    if track.song_link is not None:
        message_text += f' | {url("Other", track.song_link)}'

    return message_text


@dp.chosen_inline_result()
async def chosen_inline_result_handler(result: ChosenInlineResult) -> None:
    # todo @es3n1n: multiprocess queue
    if result.inline_message_id is None:
        return

    uri = result.result_id
    platform_name, track_id = uri.split('_', maxsplit=1)
    platform_type = SongLinkPlatformType(platform_name)

    if not db.is_user_authorized(result.from_user.id, platform_type):
        await bot.edit_message_caption(inline_message_id=result.inline_message_id, caption='Please authorize first')
        return

    client = await get_platform_from_telegram_id(result.from_user.id, platform_type)
    track = await client.get_track(track_id)
    if track is None:
        # :shrug:, there's nothing we can do
        return

    caption = track_to_caption(client, track)
    thumbnail, mp3 = await download_mp3(track)

    if mp3 is None:
        caption = f'Error: track is unavailable :(\n{caption}'
        await bot.edit_message_caption(inline_message_id=result.inline_message_id, caption=caption, parse_mode='HTML')
        return

    file_id = await cache_file(track.uri, mp3, thumbnail, track.artist, track.name, result.from_user)
    await bot.edit_message_media(media=InputMediaAudio(
        performer=track.artist,
        title=track.name,
        media=file_id,
        caption=caption,
        parse_mode='HTML',
    ), inline_message_id=result.inline_message_id)


@dp.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    result: list[InlineQueryResultArticle | InlineQueryResultAudio | InlineQueryResultCachedAudio] = list()
    is_authorized: bool = False

    feed = list()
    clients: dict[SongLinkPlatformType, PlatformClientABC] = dict()

    for platform in platforms:
        if not db.is_user_authorized(query.from_user.id, platform.type):
            continue

        is_authorized = True
        try:
            client = await get_platform_from_telegram_id(query.from_user.id, platform.type)

            async for track in client.get_current_and_recent_tracks(NUM_OF_ITEMS_TO_QUERY):
                feed.append(track)

            clients[platform.type] = client
        except Exception as e:
            logger.opt(exception=e).error('Something went wrong!')
            result.append(InlineQueryResultArticle(
                id='0',
                title='Something went wrong, dm @invlpg',
                url='https://t.me/invlpg',
                input_message_content=InputTextMessageContent(
                    message_text='Something went wrong (┛ಠ_ಠ)┛彡┻━┻'
                )
            ))
            feed.clear()
            break

    seen_uris = list()
    i: int = -1

    for track in reversed(sorted(
            feed,
            key=lambda x: (x.currently_playing, x.played_at)
    )):
        i += 1
        if track.uri in seen_uris:
            continue

        seen_uris.append(track.uri)
        client = clients[track.platform]

        if file_id := await get_cached_file_id(track.uri):
            result.append(InlineQueryResultCachedAudio(
                id=track.uri,
                audio_file_id=file_id,
                caption=track_to_caption(client, track),
                parse_mode='HTML'
            ))
            continue

        supported: bool = client.features.get('track_getters', True)

        result.append(InlineQueryResultAudio(
            id=track.uri if supported else str(i),
            audio_url=f'{config.EMPTY_MP3_FILE_URL}?{quote(track.uri)}',
            performer=track.artist,
            title=track.name,
            caption=track_to_caption(client, track),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text='downloading audio',
                        callback_data='loading'
                    )
                ]]
            ) if supported else None
        ))

    if not is_authorized:
        result.append(InlineQueryResultArticle(
            id='0',
            title='Please authorize',
            url=config.BOT_URL,
            input_message_content=InputTextMessageContent(
                message_text=f'Please {url("authorize", config.get_start_url("link"))} first (╯°□°)╯︵ ┻━┻',
                parse_mode='HTML'
            )
        ))

    if len(result) == 0:
        result.append(InlineQueryResultArticle(
            id='0',
            title='Hmm, no tracks found',
            input_message_content=InputTextMessageContent(
                message_text='No tracks found (┛ಠ_ಠ)┛彡┻━┻'
            )
        ))

    await bot.answer_inline_query(query.id, results=result, cache_time=1)  # type: ignore
