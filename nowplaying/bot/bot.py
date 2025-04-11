from aiogram import Bot, Dispatcher
from aiogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedGif,
    InlineQueryResultCachedMpeg4Gif,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedSticker,
    InlineQueryResultCachedVideo,
    InlineQueryResultCachedVoice,
    InlineQueryResultContact,
    InlineQueryResultDocument,
    InlineQueryResultGame,
    InlineQueryResultGif,
    InlineQueryResultLocation,
    InlineQueryResultMpeg4Gif,
    InlineQueryResultPhoto,
    InlineQueryResultsButton,
    InlineQueryResultVenue,
    InlineQueryResultVideo,
    InlineQueryResultVoice,
)

from nowplaying.core.config import config

from .session import BotSession


# A custom bot class that modifies some default values for the methods to reduce amount of repeated code.
class OurBot(Bot):
    async def answer_inline_query(  # noqa: PLR0913
        self,
        inline_query_id: str,
        results: list[
            InlineQueryResultCachedAudio
            | InlineQueryResultCachedDocument
            | InlineQueryResultCachedGif
            | InlineQueryResultCachedMpeg4Gif
            | InlineQueryResultCachedPhoto
            | InlineQueryResultCachedSticker
            | InlineQueryResultCachedVideo
            | InlineQueryResultCachedVoice
            | InlineQueryResultArticle
            | InlineQueryResultAudio
            | InlineQueryResultContact
            | InlineQueryResultGame
            | InlineQueryResultDocument
            | InlineQueryResultGif
            | InlineQueryResultLocation
            | InlineQueryResultMpeg4Gif
            | InlineQueryResultPhoto
            | InlineQueryResultVenue
            | InlineQueryResultVideo
            | InlineQueryResultVoice
        ],
        cache_time: int | None = -1,
        is_personal: bool | None = True,  # noqa: FBT002
        next_offset: str | None = None,
        button: InlineQueryResultsButton | None = None,
        switch_pm_parameter: str | None = None,
        switch_pm_text: str | None = None,
        request_timeout: int | None = None,
    ) -> bool:
        return await super().answer_inline_query(
            inline_query_id=inline_query_id,
            results=results,
            cache_time=cache_time,
            is_personal=is_personal,
            next_offset=next_offset,
            button=button,
            switch_pm_parameter=switch_pm_parameter,
            switch_pm_text=switch_pm_text,
            request_timeout=request_timeout,
        )


dp = Dispatcher()
bot = OurBot(token=config.BOT_TOKEN, session=BotSession())
