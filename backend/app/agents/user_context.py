"""Per-request user context for agent tool execution.

Uses a thread-safe dictionary instead of ContextVar because LangGraph
dispatches tool calls via ThreadPoolExecutor, and ContextVar values
do NOT propagate to child threads.
"""

import threading

_lock = threading.Lock()
_thread_user_map: dict[str, str] = {}


def set_user_for_thread(thread_id: str, user_id: str) -> None:
    """Register user_id for a given agent thread_id."""
    with _lock:
        _thread_user_map[thread_id] = user_id


def clear_user_for_thread(thread_id: str) -> None:
    """Remove user_id mapping for a given agent thread_id."""
    with _lock:
        _thread_user_map.pop(thread_id, None)


def get_user_for_thread(thread_id: str) -> str | None:
    """Get the user_id associated with a given agent thread_id."""
    with _lock:
        return _thread_user_map.get(thread_id)
