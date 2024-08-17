from aiogram import html
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse, RedirectResponse

from nowplaying.bot.bot import bot
from nowplaying.core.config import config
from nowplaying.core.sign import verify_sign
from nowplaying.enums.start_actions import StartAction
from nowplaying.platforms import apple, lastfm, spotify
from nowplaying.util.http import STATUS_FORBIDDEN, STATUS_TEMPORARY_REDIRECT


router = APIRouter(prefix='/ext')
redirect = RedirectResponse(
    url=config.BOT_URL,
    status_code=STATUS_TEMPORARY_REDIRECT,
)


async def send_auth_msg(telegram_id: int, platform_name: str) -> None:
    await bot.send_message(
        telegram_id,
        f'Successfully authorized in {html.bold(platform_name.title())}!',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Open inline menu',
                        switch_inline_query_current_chat='',
                    )
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


@router.get('/spotify/callback')
async def spotify_callback(code: str, state: str) -> RedirectResponse:
    telegram_id = verify_sign(state)
    await spotify.from_auth_callback(telegram_id, code)
    await send_auth_msg(telegram_id, 'spotify')
    return redirect


@router.get('/lastfm/callback')
async def lastfm_callback(token: str, state: str) -> RedirectResponse:
    telegram_id = verify_sign(state)
    await lastfm.from_auth_callback(telegram_id, token)
    await send_auth_msg(telegram_id, 'lastfm')
    return redirect


@router.get('/apple/callback')
async def apple_callback(token: str, state: str) -> RedirectResponse:
    telegram_id = verify_sign(state)
    await apple.from_auth_callback(telegram_id, token)
    await send_auth_msg(telegram_id, 'apple music')
    return redirect


@router.get('/apple/token')
async def apple_token(state: str) -> ORJSONResponse:
    try:
        verify_sign(state, check_expiration=True)
    except HTTPException:
        return ORJSONResponse(
            {
                'detail': 'session expired',
                'redirect_to': config.bot_plain_start_url(StartAction.SIGN_EXPIRED),
            },
            status_code=STATUS_FORBIDDEN,
        )

    return ORJSONResponse(
        {
            'token': apple.app.ensured_token,
        }
    )
