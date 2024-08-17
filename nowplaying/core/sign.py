import binascii
import hmac
from base64 import b64decode, b64encode
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

import orjson
from fastapi import HTTPException

from nowplaying.core.config import config
from nowplaying.util.http import STATUS_BAD_REQUEST
from nowplaying.util.time import UTC_TZ


SIGN_EXPIRES_IN = timedelta(hours=2)
SIGN_EXPIRED_EXCEPTION = HTTPException(status_code=STATUS_BAD_REQUEST, detail='This link has expired. Get a new one.')


def _hmac(payload: str) -> str:
    return hmac.new(config.STATE_SECRET.encode(), payload.encode(), sha256).hexdigest()


def _payload_to_sign(payload: Any, expires_at: int) -> str:  # noqa: ANN401
    return f'{payload}{expires_at}'


def sign(payload: Any) -> str:  # noqa: ANN401
    expires_at = int((datetime.now(tz=UTC_TZ) + SIGN_EXPIRES_IN).timestamp())
    return b64encode(
        orjson.dumps(
            {
                'h': payload,
                'e': expires_at,
                'm': _hmac(_payload_to_sign(payload, expires_at)),
            }
        )
    ).decode()


def _validate_fields(payload: Any | None, signature: str | None, expires_at: int | None) -> bool:  # noqa: ANN401
    if not isinstance(payload, int):
        return False

    if not isinstance(signature, str):
        return False

    return isinstance(expires_at, int)


def verify_sign(state: str, *, check_expiration: bool = False) -> Any:  # noqa: ANN401
    try:
        loaded = orjson.loads(b64decode(state).decode())
    except (binascii.Error, orjson.JSONDecodeError):
        loaded = None

    if not isinstance(loaded, dict):
        raise SIGN_EXPIRED_EXCEPTION

    payload = loaded.get('h', None)
    signature = loaded.get('m', None)
    expires_at = loaded.get('e', None)

    if not _validate_fields(payload, signature, expires_at):
        raise SIGN_EXPIRED_EXCEPTION

    to_sign: str = _payload_to_sign(payload, expires_at)

    matches = hmac.compare_digest(signature, _hmac(to_sign))
    if check_expiration and expires_at < int(datetime.now(tz=UTC_TZ).timestamp()):
        matches = False

    if not matches:
        raise SIGN_EXPIRED_EXCEPTION

    return payload
