from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pylast import WSError
from spotipy import SpotifyOauthError

from ..bot.bot import bot
from ..core.config import config
from ..core.sign import verify_sign
from ..platforms import lastfm, spotify
from ..util.logger import logger


router = APIRouter(prefix='/ext')
redirect = RedirectResponse(
    url=config.BOT_URL,
    status_code=307,
)


async def send_auth_msg(telegram_id: int, platform_name: str) -> None:
    await bot.send_message(
        telegram_id,
        f'Successfully authorized in {platform_name}! '
        'Check out the inline menu to see your recent tracks'
    )


@router.get('/spotify/callback')
async def spotify_callback(code: str, state: str):
    telegram_id = verify_sign(state)

    try:
        await spotify.from_auth_callback(telegram_id, code)
    except SpotifyOauthError as e:
        if e.error_description in ['Invalid authorization code']:
            return 'Got an invalid authorization code, please try again'

        logger.opt(exception=e).error('Unable to authorize')
        return 'Something went wrong, dm @invlpg on telegram'

    await send_auth_msg(telegram_id, 'spotify')
    return redirect


@router.get('/lastfm/callback')
async def lastfm_callback(token: str, state: str):
    telegram_id = verify_sign(state)

    try:
        await lastfm.from_auth_callback(telegram_id, token)
    except WSError:
        return 'Got an invalid authorization code, please try again'

    await send_auth_msg(telegram_id, 'lastfm')
    return redirect
