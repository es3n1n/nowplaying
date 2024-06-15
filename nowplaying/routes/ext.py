from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from spotipy import SpotifyOauthError

from ..bot.bot import bot
from ..core.config import config
from ..core.sign import verify_sign
from ..core.spotify import spotify
from ..util.logger import logger


router = APIRouter(prefix='/ext')


@router.get('/spotify/callback')
async def spotify_callback(code: str, state: str):
    telegram_id = verify_sign(state)

    try:
        spotify.from_auth_code(telegram_id, code)
    except SpotifyOauthError as e:
        if e.error_description in ['Invalid authorization code']:
            return 'Got an invalid authorization code, please try again'

        logger.opt(exception=e).error('Unable to authorize')
        return 'Something went wrong, dm @invlpg on telegram'

    await bot.send_message(telegram_id, 'Successfully authorized! Check out the inline menu to see your recent tracks')
    return RedirectResponse(
        url=config.BOT_URL,
        status_code=307,
    )
