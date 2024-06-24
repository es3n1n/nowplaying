from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse, RedirectResponse

from ..bot.bot import bot
from ..core.config import config
from ..core.sign import verify_sign
from ..enums.start_actions import StartAction
from ..platforms import apple, lastfm, spotify
from ..util.http import STATUS_FORBIDDEN, STATUS_TEMPORARY_REDIRECT


router = APIRouter(prefix='/ext')
redirect = RedirectResponse(
    url=config.BOT_URL,
    status_code=STATUS_TEMPORARY_REDIRECT,
)


async def send_auth_msg(telegram_id: int, platform_name: str) -> None:
    await bot.send_message(
        telegram_id,
        (
            f'Successfully authorized in {platform_name.title()}! '
            + 'Check out the inline menu to see your recent tracks'
        ),
    )


@router.get('/spotify/callback')
async def spotify_callback(code: str, state: str):
    telegram_id = verify_sign(state)
    await spotify.from_auth_callback(telegram_id, code)
    await send_auth_msg(telegram_id, 'spotify')
    return redirect


@router.get('/lastfm/callback')
async def lastfm_callback(token: str, state: str):
    telegram_id = verify_sign(state)
    await lastfm.from_auth_callback(telegram_id, token)
    await send_auth_msg(telegram_id, 'lastfm')
    return redirect


@router.get('/apple/callback')
async def apple_callback(token: str, state: str):
    telegram_id = verify_sign(state)
    await apple.from_auth_callback(telegram_id, token)
    await send_auth_msg(telegram_id, 'apple music')
    return redirect


@router.get('/apple/token')
async def apple_token(state: str):
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

    return ORJSONResponse({
        'token': apple.app.ensured_token,
    })
