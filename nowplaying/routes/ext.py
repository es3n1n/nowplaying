from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse, RedirectResponse

from nowplaying.bot.handlers.start import send_auth_msg
from nowplaying.core.config import config
from nowplaying.core.sign import verify_sign
from nowplaying.enums.start_actions import StartAction
from nowplaying.platforms import PlatformABC, apple, lastfm, spotify, yandex
from nowplaying.util.http import STATUS_FORBIDDEN, STATUS_TEMPORARY_REDIRECT


router = APIRouter(prefix='/ext')
redirect = RedirectResponse(
    url=config.BOT_URL,
    status_code=STATUS_TEMPORARY_REDIRECT,
)


async def _proceed_auth(platform: PlatformABC, state: str, arg: str) -> RedirectResponse:
    telegram_id = verify_sign(state)
    await platform.from_auth_callback(telegram_id, arg)
    await send_auth_msg(telegram_id, platform.type)
    return redirect


@router.get('/spotify/callback')
async def spotify_callback(state: str, code: str) -> RedirectResponse:
    return await _proceed_auth(spotify, state, code)


@router.get('/lastfm/callback')
async def lastfm_callback(state: str, token: str) -> RedirectResponse:
    return await _proceed_auth(lastfm, state, token)


@router.get('/yandex/callback')
async def yandex_callback(state: str, access_token: str) -> RedirectResponse:
    return await _proceed_auth(yandex, state, access_token)


@router.get('/apple/callback')
async def apple_callback(state: str, token: str) -> RedirectResponse:
    return await _proceed_auth(apple, state, token)


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
