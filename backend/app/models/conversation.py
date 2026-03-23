"""Conversation/thread mapping models."""
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ChatThreadModel(BaseModel):
    """Maps an authenticated user to a chat thread id."""
    user_id: str
    thread_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
