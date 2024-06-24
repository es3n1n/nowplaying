
STATUS_TEMPORARY_REDIRECT: int = 307
STATUS_OK: int = 200
STATUS_NO_CONTENT: int = 204
STATUS_BAD_REQUEST: int = 400
STATUS_NOT_FOUND: int = 404


def is_clientside_error(http_code: int) -> bool:
    return 400 <= http_code <= 499  # noqa: WPS432
