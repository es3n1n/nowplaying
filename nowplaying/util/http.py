from nowplaying.util.user_agents import get_random_user_agent


STATUS_OK: int = 200
STATUS_NO_CONTENT: int = 204
STATUS_TEMPORARY_REDIRECT: int = 307
STATUS_BAD_REQUEST: int = 400
STATUS_FORBIDDEN: int = 403
STATUS_NOT_FOUND: int = 404

STATUS_CLIENTSIDE_MIN: int = 400
STATUS_CLIENTSIDE_MAX: int = 499

STATUS_SERVERSIDE_MIN: int = 500
STATUS_SERVERSIDE_MAX: int = 599


def is_clientside_error(http_code: int) -> bool:
    return STATUS_CLIENTSIDE_MIN <= http_code <= STATUS_CLIENTSIDE_MAX


def is_serverside_error(http_code: int) -> bool:
    return STATUS_SERVERSIDE_MIN <= http_code <= STATUS_SERVERSIDE_MAX


def get_headers(
    *,
    legitimate_headers: bool = False,
    origin: str | None = None,
    referer: str | None = None,
    chrome_user_agent: bool = False,
) -> dict[str, str]:
    headers = {'User-Agent': 'playinnow 1.0', 'Accept': 'application/json'}
    if legitimate_headers:
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Priority': 'u=1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'User-Agent': get_random_user_agent(chrome=chrome_user_agent),
        }

    if origin is not None:
        headers['Origin'] = origin

    if referer is not None:
        headers['Referer'] = referer

    return headers
