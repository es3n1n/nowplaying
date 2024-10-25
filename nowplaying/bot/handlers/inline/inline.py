from asyncio import TaskGroup
from urllib.parse import quote

from aiogram import html, types
from aiogram.enums import ParseMode

from nowplaying.bot.bot import bot, dp
from nowplaying.bot.caching import get_cached_file_id
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track
from nowplaying.platforms import PlatformClientABC, get_platform_from_telegram_id, get_platform_track
from nowplaying.util.string import extract_from_query

from .inline_utils import NUM_OF_ITEMS_TO_QUERY, track_to_caption


async def parse_inline_result_query(
    inline_result: types.ChosenInlineResult,
) -> tuple[PlatformClientABC | None, Track | None]:
    uri = inline_result.result_id
    platform_name, track_id = extract_from_query(uri, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(inline_result.from_user.id, platform_type):
        await bot.edit_message_caption(
            inline_message_id=inline_result.inline_message_id,
            caption='Please authorize first',
        )
        return None, None

    return await get_platform_track(track_id, inline_result.from_user.id, platform_type)


async def _fetch_feed(
    clients: dict[SongLinkPlatformType, PlatformClientABC],
    feed: list[Track],
    user_id: int,
    platform_type: SongLinkPlatformType,
) -> None:
    client = await get_platform_from_telegram_id(user_id, platform_type)

    feed.extend([track async for track in client.get_current_and_recent_tracks(NUM_OF_ITEMS_TO_QUERY)])
    clients[platform_type] = client


async def fetch_feed_and_clients(
    query_id: str,
    user_id: int,
) -> tuple[list[Track] | None, dict[SongLinkPlatformType, PlatformClientABC] | None]:
    feed: list[Track] = []
    clients: dict[SongLinkPlatformType, PlatformClientABC] = {}

    authorized_platforms = await db.get_user_authorized_platforms(user_id)

    if not authorized_platforms:
        await bot.answer_inline_query(
            inline_query_id=query_id,
            results=[
                types.InlineQueryResultArticle(
                    id='0',
                    title='Please authorize',
                    url=config.BOT_URL,
                    input_message_content=types.InputTextMessageContent(
                        message_text=f'Please {html.link("authorize", config.BOT_URL)} first (╯°□°)╯︵ ┻━┻',
                        parse_mode=ParseMode.HTML,
                    ),
                ),
            ],
            cache_time=1,
        )
        return None, None

    async with TaskGroup() as group:
        for platform in authorized_platforms:
            group.create_task(_fetch_feed(clients, feed, user_id, platform))

    return feed, clients


async def feed_to_inline_results(
    feed: list[Track],
    clients: dict[SongLinkPlatformType, PlatformClientABC],
) -> list[types.InlineQueryResultArticle | types.InlineQueryResultAudio | types.InlineQueryResultCachedAudio]:
    seen_uris: set[str] = set()
    sorted_feed = sort_feed(feed)

    return [
        await create_result_item(track, clients, seen_uris, index)
        for index, track in enumerate(sorted_feed)
        if track.uri not in seen_uris
    ]


def sort_feed(feed: list[Track]) -> list[Track]:
    return sorted(
        feed,
        key=lambda track_item: (track_item.currently_playing, track_item.played_at),
        reverse=True,
    )


async def create_result_item(
    track: Track,
    clients: dict[SongLinkPlatformType, PlatformClientABC],
    seen_uris: set,
    index: int,
) -> types.InlineQueryResultAudio | types.InlineQueryResultCachedAudio:
    seen_uris.add(track.uri)
    client = clients[track.platform]

    cached_file_id = await get_cached_file_id(track.uri)
    if cached_file_id:
        return create_cached_audio_result(track, cached_file_id, client)

    return create_audio_result(track, client, index=index, multiple_clients=len(clients) > 1)


def create_cached_audio_result(
    track: Track,
    cached_file_id: str,
    client: PlatformClientABC,
) -> types.InlineQueryResultCachedAudio:
    return types.InlineQueryResultCachedAudio(
        id=track.uri,
        audio_file_id=cached_file_id,
        caption=track_to_caption(client, track),
        parse_mode=ParseMode.HTML,
    )


def create_audio_result(
    track: Track,
    client: PlatformClientABC,
    *,
    index: int,
    multiple_clients: bool,
) -> types.InlineQueryResultAudio:
    is_getter_available = client.features.get(PlatformFeature.TRACK_GETTERS, True)
    is_track_available = track.is_available
    can_proceed = is_getter_available and is_track_available

    name = track.name
    if multiple_clients:
        name += f' ({track.platform.name.capitalize()})'

    uri_for_placeholder = track.uri
    # Swap the uri for unavailable tracks (their id will be None)
    if not is_track_available:
        # We still want it to cache on the telegram side, so instead of using random stuff let's use the url
        uri_for_placeholder = track.url

    return types.InlineQueryResultAudio(
        id=track.uri if can_proceed else str(index),
        audio_url=f'{config.EMPTY_MP3_FILE_URL}?{quote(uri_for_placeholder)}',
        performer=track.artist,
        title=name,
        caption=track_to_caption(
            client, track, is_getter_available=is_getter_available, is_track_available=is_track_available
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text='Downloading the audio',
                        callback_data='loading',
                    ),
                ]
            ],
        )
        if can_proceed
        else None,
    )


@dp.inline_query()
async def inline_query_handler(query: types.InlineQuery) -> None:
    feed, clients = await fetch_feed_and_clients(query.id, query.from_user.id)
    if feed is None or clients is None:
        return

    result_items = await feed_to_inline_results(feed, clients)
    if not result_items:
        result_items.append(
            types.InlineQueryResultArticle(
                id='0',
                title='Hmm, no recent tracks found',
                input_message_content=types.InputTextMessageContent(
                    message_text='No recent tracks found (┛ಠ_ಠ)┛彡┻━┻',
                ),
            )
        )

    await bot.answer_inline_query(query.id, results=result_items, cache_time=1)  # type: ignore[arg-type]
