"""Conversation services for thread-id lifecycle and mapping persistence."""

from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_chat_threads_collection
from app.database.mongo import mongo_available
from app.models.conversation import ChatThreadModel


def _get_collection():
    if not mongo_available():
        return None
    try:
        return get_chat_threads_collection()
    except Exception as e:
        return None

def create_thread_for_user(user_id: str) -> dict:
    """Create and persist a new thread mapping for the authenticated user."""
    thread_id = str(uuid4())
    thread = ChatThreadModel(user_id=user_id, thread_id=thread_id)
    collection = _get_collection()
    if collection is not None:
        collection.insert_one(thread.model_dump())
    return {
        "user_id": user_id,
        "thread_id": thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


def user_owns_thread(user_id: str, thread_id: str) -> bool:
    """Return True when thread_id belongs to user_id."""
    collection = _get_collection()
    if collection is None:
        return True
    collection = get_chat_threads_collection()
    return collection.find_one({"user_id": user_id, "thread_id": thread_id}) is not None


def get_user_id_for_thread(thread_id: str) -> str | None:
    """Return the owner user_id for a thread_id, or None when not found."""
    collection = _get_collection()
    if collection is None:
        return None
    doc = collection.find_one({"thread_id": thread_id}, {"_id": 0, "user_id": 1})
    if not doc:
        return None
    return doc.get("user_id")


def touch_thread(user_id: str, thread_id: str) -> None:
    """Update thread activity timestamp after successful chat activity."""
    collection = _get_collection()
    if collection is None:
        return
    collection.update_one(
        {"user_id": user_id, "thread_id": thread_id},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
    )


def get_user_threads(user_id: str) -> list[dict]:
    """List all thread ids for a user, newest activity first."""
    collection = _get_collection()
    if collection is None:
        return []
    docs = list(
        collection.find({"user_id": user_id}, {"_id": 0, "user_id": 0}).sort("updated_at", -1)
    )
    for doc in docs:
        for key in ("created_at", "updated_at"):
            if isinstance(doc.get(key), datetime):
                doc[key] = doc[key].isoformat()
    return docs
