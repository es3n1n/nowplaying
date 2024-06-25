from urllib.parse import ParseResult
from urllib.parse import urlparse as _urlparse


def urlparse(url: str, keep_www: bool = False) -> ParseResult:
    parsed = _urlparse(url)

    # We dont need www.
    if not keep_www and parsed.netloc.startswith('www.'):
        parsed = parsed._replace(netloc=parsed.netloc[4:])  # noqa: WPS437

    return parsed
