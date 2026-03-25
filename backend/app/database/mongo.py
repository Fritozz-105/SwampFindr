"""MongoDB database connection and management."""
import os
import certifi
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

# Global MongoDB client instance
_mongo_client = None
_db = None


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = os.getenv('URI')
        if not mongo_uri:
            raise ValueError("URI environment variable not set")

        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            tlsCAFile=certifi.where()
        )
    return _mongo_client


def get_db() -> Database:
    """Get the Property database."""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client['Property']
    return _db


def get_listings_collection() -> Collection:
    """Get the Listings collection."""
    db = get_db()
    return db['Listings']


def get_units_collection() -> Collection:
    """Get the Units collection."""
    db = get_db()
    return db['Units']


def get_userdata_db() -> Database:
    """Get the UserData database."""
    client = get_mongo_client()
    return client['UserData']


def get_profiles_collection() -> Collection:
    """Get the Profiles collection from the UserData database."""
    db = get_userdata_db()
    return db['Profiles']


def get_chat_threads_collection() -> Collection:
    """Get the ChatThreads collection from the UserData database."""
    db = get_userdata_db()
    return db['ChatThreads']


def get_search_history_collection() -> Collection:
    """Get the SearchHistory collection from the UserData database."""
    db = get_userdata_db()
    return db['SearchHistory']


def init_db(app):
    """Initialize database connection with Flask app."""
    with app.app_context():
        try:
            client = get_mongo_client()
            # Test connection
            client.admin.command('ping')
            app.logger.info("✓ Connected to MongoDB Atlas")
            # Ensure unique index on Profiles.user_id
            get_profiles_collection().create_index("user_id", unique=True, background=True)
            app.logger.info("✓ Ensured unique index on Profiles.user_id")
            get_chat_threads_collection().create_index("thread_id", unique=True, background=True)
            get_chat_threads_collection().create_index(
                [("user_id", 1), ("updated_at", -1)],
                background=True,
            )
            app.logger.info("✓ Ensured ChatThreads indexes")
            get_search_history_collection().create_index(
                [("user_id", 1), ("created_at", -1)],
                background=True,
            )
            app.logger.info("Ensured SearchHistory indexes")
        except Exception as e:
            app.logger.error(f"MongoDB connection failed: {e}")
            raise


def close_db():
    """Close MongoDB connection."""
    global _mongo_client, _db
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _db = None
