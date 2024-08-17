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
