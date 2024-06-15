from fastapi import FastAPI
from uvicorn import run
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


app = FastAPI()

auth_manager = SpotifyOAuth(
    client_id='',
    client_secret='',
    redirect_uri='http://127.0.0.1:1337/ext/spotify/callback',
    open_browser=True,
)
spotify = Spotify(auth_manager=auth_manager)


@app.get('/ext/spotify/callback')
async def spotify_callback(code: str):
    print('got the code', code)

    auth_manager.get_authorization_code()


def main() -> None:
    print(auth_manager.get_authorize_url())
    run(app, host='0.0.0.0', port=1337)


if __name__ == '__main__':
    main()
