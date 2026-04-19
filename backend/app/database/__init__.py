"""Database package initialization."""
from app.database.mongo import (
    get_db,
    get_listings_collection,
    get_units_collection,
    get_profiles_collection,
    get_chat_threads_collection,
    get_search_history_collection,
    get_gmail_auth_collection,
    get_email_history_collection,
    init_db,
    close_db
)

__all__ = [
    'get_db',
    'get_listings_collection',
    'get_units_collection',
    'get_profiles_collection',
    'get_chat_threads_collection',
    'get_search_history_collection',
    'get_gmail_auth_collection',
    'get_email_history_collection',
    'init_db',
    'close_db'
]
