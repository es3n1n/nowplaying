import hmac
from hashlib import sha256
from typing import Any

from fastapi import HTTPException
from orjson import JSONDecodeError, dumps, loads

from .config import config


def _hmac(payload: str) -> str:
    return hmac.new(config.STATE_SECRET.encode(), payload.encode(), sha256).hexdigest()


def sign(payload: Any) -> str:
    return dumps({
        'h': payload,
        'm': _hmac(str(payload))
    }).decode()


def verify_sign(state: str) -> Any:
    try:
        loaded = loads(state)
        assert isinstance(loaded, dict)

        payload = loaded['h']
        assert isinstance(payload, int)

        signature = loaded['m']
        assert isinstance(signature, str)
    except (JSONDecodeError, KeyError, AssertionError):
        raise HTTPException(status_code=400, detail='Invalid state')

    if not hmac.compare_digest(signature, _hmac(str(payload))):
        raise HTTPException(status_code=400, detail='Invalid signature')

    return payload
