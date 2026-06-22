"""Valkey (Redis-compatible) caching layer."""
import json
import redis

from src.config import VALKEY_HOST, VALKEY_PORT, CACHE_TTL_SECONDS

_client = None


def get_client():
    """Return Valkey client, create if not exists."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = redis.Redis(
            host=VALKEY_HOST,
            port=VALKEY_PORT,
            decode_responses=True
        )
    return _client


def get_cached_temperature():
    """Return cached temperature data or None if not found/expired."""
    try:
        data = get_client().get("temperature")
        if data:
            return json.loads(data)
    except Exception:  # pylint: disable=broad-except
        return None
    return None


def set_cached_temperature(data):
    """Store temperature data in cache with TTL."""
    try:
        get_client().setex(
            "temperature",
            CACHE_TTL_SECONDS,
            json.dumps(data)
        )
    except Exception:  # pylint: disable=broad-except
        pass


def get_cache_age():
    """Return age of cached data in seconds, or None if no cache exists."""
    try:
        ttl = get_client().ttl("temperature")
        if ttl == -2:
            return None          # key doesn't exist
        if ttl == -1:
            return 0             # key exists but no expiry = treat as fresh
        return CACHE_TTL_SECONDS - ttl
    except Exception:            # pylint: disable=broad-except
        return None              # valkey unreachable


def is_cache_fresh():
    """Return True if cache exists and is less than 5 minutes old."""
    age = get_cache_age()
    if age is None:
        # key doesn't exist = fresh start, not the same as stale
        # only fail readyz if cache existed and went stale
        return True
    return age < CACHE_TTL_SECONDS
