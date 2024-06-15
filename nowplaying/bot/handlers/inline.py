from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions
from aiostream.stream import enumerate as a_enumerate

from ...core.config import config
from ...core.spotify import spotify
from ...database import db
from ...models.track import Track
from ...util.string import escape_html
from ..bot import bot, dp


def url(text: str, href: str) -> str:
    return f'<a href="{href}">{text}</a>'


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

    result: list[InlineQueryResultArticle] = list()
    track: Track
    async for i, track in a_enumerate(client.get_current_and_recent_tracks()):  # type: ignore[arg-type]
        if not isinstance(track, Track):
            continue

        play_url = config.get_start_url(track.uri)  # type: ignore[attr-defined]

        message_text = f'{escape_html(track.artist)} - {escape_html(track.name)}\n'  # type: ignore[attr-defined]
        message_text += f'\n{url("Spotify", track.url)} ({url("▶️", play_url)})'  # type: ignore[attr-defined]
        if track.song_link is not None:  # type: ignore[attr-defined]
            message_text += f' | {url("Other", track.song_link)}'  # type: ignore[attr-defined]

        result.append(
            InlineQueryResultArticle(
                id=str(i),
                title=f'{track.artist} - {track.name}',  # type: ignore[attr-defined]
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode='HTML',
                    link_preview_options=LinkPreviewOptions(
                        is_disabled=True
                    )
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
