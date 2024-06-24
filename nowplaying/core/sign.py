import hmac
from hashlib import sha256
from typing import Any

import orjson
from fastapi import HTTPException

from ..util.http import STATUS_BAD_REQUEST
from .config import config


def _hmac(payload: str) -> str:
    return hmac.new(config.STATE_SECRET.encode(), payload.encode(), sha256).hexdigest()


def sign(payload: Any) -> str:
    return orjson.dumps({
        'h': payload,
        'm': _hmac(str(payload)),
    }).decode()


def verify_sign(state: str) -> Any:
    try:
        loaded = orjson.loads(state)
    except orjson.JSONDecodeError:
        loaded = None

    if not isinstance(loaded, dict):
        raise HTTPException(status_code=STATUS_BAD_REQUEST, detail='Invalid state')

    payload = loaded.get('h', None)
    signature = loaded.get('m', None)

    if not isinstance(payload, int) or not isinstance(signature, str):
        raise HTTPException(status_code=STATUS_BAD_REQUEST, detail='Invalid args')

    if not hmac.compare_digest(signature, _hmac(str(payload))):
        raise HTTPException(status_code=STATUS_BAD_REQUEST, detail='Invalid signature')

    return payload
