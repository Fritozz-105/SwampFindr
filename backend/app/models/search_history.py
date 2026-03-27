"""Search history model."""
from pydantic import BaseModel
from typing import List
from datetime import datetime


class SearchHistoryModel(BaseModel):
    user_id: str
    query: str
    result_listing_ids: List[str]
    result_count: int
    created_at: datetime
