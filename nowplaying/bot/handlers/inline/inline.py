from asyncio import TaskGroup
from urllib.parse import quote

from aiogram import types
from aiogram.enums import ParseMode

from nowplaying.bot.bot import bot, dp
from nowplaying.core.config import config
from nowplaying.core.database import db
from nowplaying.enums.callback_buttons import CallbackButton
from nowplaying.enums.platform_features import PlatformFeature
from nowplaying.models.song_link import SongLinkPlatformType
from nowplaying.models.track import Track
from nowplaying.models.user_config import UserConfig
from nowplaying.platforms import PlatformClientABC, get_platform_from_telegram_id, get_platform_track
from nowplaying.util.string import encode_query, extract_from_query

from .inline_utils import NUM_OF_ITEMS_TO_QUERY, track_to_caption


async def parse_track_from_uri(user_id: int, uri: str) -> tuple[PlatformClientABC | None, Track | None]:
    platform_name, track_id = extract_from_query(uri, arguments_count=2)
    platform_type = SongLinkPlatformType(platform_name)

    if not await db.is_user_authorized(user_id, platform_type):
        msg = f'User is not authorized {user_id=}'
        raise ValueError(msg)

    return await get_platform_track(track_id, user_id, platform_type)


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
            button=types.InlineQueryResultsButton(
                text='Authorize',
                # We don't really care about start parameter, but it can't be an empty string
                start_parameter='hello',
            ),
            results=[],
        )
        return None, None

    async with TaskGroup() as group:
        for platform in authorized_platforms:
            group.create_task(_fetch_feed(clients, feed, user_id, platform))

    return feed, clients


async def feed_to_inline_results(
    feed: list[Track],
    clients: dict[SongLinkPlatformType, PlatformClientABC],
    user_config: UserConfig,
) -> list[types.InlineQueryResultArticle | types.InlineQueryResultAudio]:
    seen_uris: set[str] = set()
    sorted_feed = sort_feed(feed)

    return [
        await create_result_item(track, clients, user_config, seen_uris, index)
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
    user_config: UserConfig,
    seen_uris: set,
    index: int,
) -> types.InlineQueryResultAudio:
    seen_uris.add(track.uri)
    client = clients[track.platform]

    is_getter_available = client.features.get(PlatformFeature.TRACK_GETTERS, True)
    is_track_available = track.is_available
    can_proceed = is_getter_available and is_track_available

    name = track.name
    if len(clients) > 0:
        name += f' ({user_config.text(track.platform.name.capitalize())})'

    uri_for_placeholder = track.uri
    # Swap the uri for unavailable tracks (their id will be None)
    if not is_track_available:
        # We still want it to cache on the telegram side, so instead of using random stuff, let's use the url
        uri_for_placeholder = track.url

    return types.InlineQueryResultAudio(
        id=track.uri if can_proceed else str(index),
        audio_url=f'{config.EMPTY_MP3_FILE_URL}?{quote(uri_for_placeholder)}',
        performer=track.artist,
        title=name,
        caption=await track_to_caption(
            user_config,
            client,
            track,
            quality=None,
            is_getter_available=is_getter_available,
            is_track_available=is_track_available,
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=user_config.text('🎲 Downloading.. (click to requeue downloading)'),
                        callback_data=encode_query(CallbackButton.LOADING, track.uri),
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

    user_config = await db.get_user_config(query.from_user.id)
    result_items = await feed_to_inline_results(feed, clients, user_config)
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

    await bot.answer_inline_query(query.id, results=result_items)  # type: ignore[arg-type]
