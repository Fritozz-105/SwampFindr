"""Flask extensions (initialized before routes to avoid circular imports)."""
from flask import g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _get_rate_limit_key():
    """Use authenticated user_id if available, otherwise fall back to IP."""
    user_id = getattr(g, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address()


limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[],
    storage_uri="memory://",
)
