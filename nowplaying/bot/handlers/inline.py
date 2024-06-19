from asyncio import TaskGroup
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
from ...enums.platform_features import PlatformFeature
from ...models.song_link import SongLinkPlatformType
from ...models.track import Track
from ...platforms import PlatformClientABC, get_platform_from_telegram_id
from ..bot import bot, dp
from ..caching import cache_file, get_cached_file_id


# Only 2 because for some fxxcked up platforms like lastfm it takes so much time to gather all the info
NUM_OF_ITEMS_TO_QUERY: int = 2


def url(text: str, href: str) -> str:
    return f'<a href="{href}">{text}</a>'


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
        message_text += 'Error: track is unavailable :(\n'

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

    caption = track_to_caption(client, track, is_getter_available=True)
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

    feed = list()
    clients: dict[SongLinkPlatformType, PlatformClientABC] = dict()

    authorized_platforms = db.get_user_authorized_platforms(query.from_user.id)
    authorized_in_multiple_platforms: bool = len(authorized_platforms) > 1

    if len(authorized_platforms) == 0:
        await bot.answer_inline_query(
            inline_query_id=query.id,
            results=[
                InlineQueryResultArticle(
                    id='0',
                    title='Please authorize',
                    url=config.BOT_URL,
                    input_message_content=InputTextMessageContent(
                        message_text=f'Please {url("authorize", config.get_start_url("link"))} first (╯°□°)╯︵ ┻━┻',
                        parse_mode='HTML'
                    )
                )
            ],
            cache_time=1
        )
        return

    async def proceed_platform(platform_type: SongLinkPlatformType) -> None:
        nonlocal clients
        client = await get_platform_from_telegram_id(query.from_user.id, platform_type)

        async for track in client.get_current_and_recent_tracks(NUM_OF_ITEMS_TO_QUERY):
            feed.append(track)

        clients[platform_type] = client

    async with TaskGroup() as group:
        [group.create_task(proceed_platform(platform)) for platform in authorized_platforms]

    seen_uris = list()

    for i, track in enumerate(reversed(sorted(
            feed,
            key=lambda x: (x.currently_playing, x.played_at)
    ))):
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

        is_getter_available: bool = client.features.get(PlatformFeature.TRACK_GETTERS, True)
        is_track_available: bool = track.is_available

        can_proceed = is_getter_available and is_track_available

        title: str = track.full_title
        if authorized_in_multiple_platforms:
            title = f'({track.platform.value.capitalize()}) {title}'

        result.append(InlineQueryResultAudio(
            id=track.uri if can_proceed else str(i),
            audio_url=f'{config.EMPTY_MP3_FILE_URL}?{quote(track.uri)}',
            title=title,
            caption=track_to_caption(client, track, is_getter_available, is_track_available),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text='downloading audio',
                        callback_data='loading'
                    )
                ]]
            ) if can_proceed else None
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
