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
from ...core.spotify import spotify
from ...database import db
from ...downloader import download_mp3
from ...models.track import Track
from ..bot import bot, dp
from ..caching import cache_file, get_cached_file_id


def url(text: str, href: str) -> str:
    return f'<a href="{href}">{text}</a>'


def track_to_caption(track: Track) -> str:
    play_url = config.get_start_url(track.uri)
    message_text = f'{url("Spotify", track.url)} ({url("▶️", play_url)})'
    if track.song_link is not None:
        message_text += f' | {url("Other", track.song_link)}'
    return message_text


@dp.update()
async def upd(x):
    print(x)


@dp.chosen_inline_result()
async def chosen_inline_result_handler(result: ChosenInlineResult) -> None:
    if not result.result_id.startswith('spotify:track:') or result.inline_message_id is None:
        return

    if not db.is_user_authorized(result.from_user.id):
        await bot.edit_message_caption(inline_message_id=result.inline_message_id, caption='Please authorize first')
        return

    client = spotify.from_telegram_id(result.from_user.id)
    track = await client.get_track(result.result_id)
    if track is None:
        await bot.edit_message_caption(inline_message_id=result.inline_message_id, caption='Something went wrong')
        return

    caption = track_to_caption(track)
    mp3 = await download_mp3(track)

    if mp3 is None:
        caption = f'Error: track is unavailable :(\n{caption}'
        await bot.edit_message_caption(inline_message_id=result.inline_message_id, caption=caption)
        return

    file_id = await cache_file(track.uri, mp3, track.artist, track.name, track.title, result.from_user)
    await bot.edit_message_media(media=InputMediaAudio(
        performer=track.artist,
        title=track.name,
        media=file_id,
        caption=caption,
        parse_mode='HTML',
    ), inline_message_id=result.inline_message_id)


@dp.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    if not db.is_user_authorized(query.from_user.id):
        await bot.answer_inline_query(query.id, results=[
            InlineQueryResultArticle(
                id='0',
                title='Please authorize',
                url=config.BOT_URL,
                input_message_content=InputTextMessageContent(
                    message_text=f'Please {url("authorize", config.get_start_url("link"))} first (╯°□°)╯︵ ┻━┻',
                    parse_mode='HTML'
                )
            )
        ], cache_time=1)
        return

    client = spotify.from_telegram_id(query.from_user.id)

    result: list[InlineQueryResultArticle | InlineQueryResultAudio | InlineQueryResultCachedAudio] = list()
    i: int = -1
    async for track in client.get_current_and_recent_tracks():
        i += 1
        if not isinstance(track, Track):
            continue

        if file_id := await get_cached_file_id(track.uri):
            result.append(InlineQueryResultCachedAudio(
                id=str(i),
                audio_file_id=file_id,
                caption=track_to_caption(track),
                parse_mode='HTML'
            ))
            continue

        result.append(
            InlineQueryResultAudio(
                id=track.uri,
                audio_url=f'{config.EMPTY_MP3_FILE_URL}?{quote(track.uri)}',
                title=f'{track.title}',
                caption=track_to_caption(track),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text='downloading audio', callback_data='loading')
                        ]
                    ]
                )
            )
        )

    if len(result) == 0:
        result.append(InlineQueryResultArticle(
            id='0',
            title='Hmm, no tracks found',
            input_message_content=InputTextMessageContent(
                message_text='No tracks found (┛ಠ_ಠ)┛彡┻━┻'
            )
        ))

    await bot.answer_inline_query(query.id, results=result, cache_time=1)  # type: ignore
