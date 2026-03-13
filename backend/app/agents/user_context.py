"""Per-request user context for agent tool execution."""

from contextvars import ContextVar, Token

_current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)


def set_current_user_id(user_id: str | None) -> Token:
    # Set the current authenticated user id for tool calls
    return _current_user_id.set(user_id)


def reset_current_user_id(token: Token) -> None:
    # Reset the current authenticated user id to previous state.
    _current_user_id.reset(token)


def get_current_user_id() -> str | None:
    # Get the current authenticated user id, if available.
    return _current_user_id.get()
