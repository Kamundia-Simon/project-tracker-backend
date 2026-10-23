"""Small Redis-backed cache helper for expensive read queries — see docs/decisions/0007."""

import json
import os
from typing import Any

import redis
from dotenv import load_dotenv

load_dotenv()

_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)


def cache_get(key: str) -> Any | None:
    raw = _client.get(key)
    return json.loads(raw) if raw else None


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    _client.setex(key, ttl_seconds, json.dumps(value, default=str))


def cache_invalidate(prefix: str) -> None:
    for key in _client.scan_iter(match=f"{prefix}*"):
        _client.delete(key)
