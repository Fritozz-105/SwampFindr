"""MongoDB database connection and management."""
import os
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
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=10000
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


def get_profiles_collection() -> Collection:
    """Get the Profiles collection."""
    db = get_db()
    return db['Profiles']


def init_db(app):
    """Initialize database connection with Flask app."""
    with app.app_context():
        try:
            client = get_mongo_client()
            # Test connection
            client.admin.command('ping')
            app.logger.info("✓ Connected to MongoDB Atlas")
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
