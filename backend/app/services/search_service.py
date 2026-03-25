"""Search service — Pinecone query, MongoDB hydration, history storage."""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_listings_collection, get_units_collection, get_search_history_collection
from app.services.profile_service import get_profile_by_user_id
from app.services.pinecone_service import query_records

logger = logging.getLogger(__name__)


def _attach_units(listings: list) -> list:
    """Attach units from the Units collection to each listing."""
    if not listings:
        return listings

    listing_ids = [l["listing_id"] for l in listings]
    units_collection = get_units_collection()
    all_units = list(units_collection.find(
        {"listing_id": {"$in": listing_ids}},
        {"_id": 0},
    ))

    units_by_listing = {}
    for unit in all_units:
        if isinstance(unit.get("availability"), datetime):
            unit["availability"] = unit["availability"].isoformat()
        lid = unit["listing_id"]
        units_by_listing.setdefault(lid, []).append(unit)

    for listing in listings:
        listing["units"] = units_by_listing.get(listing["listing_id"], [])

    return listings


def search_listings(user_id: str, query: str, top_k: int = 50) -> dict:
    """
    Search listings via Pinecone vector similarity.

    1. Pass query text to Pinecone (handles embedding internally)
    2. Hydrate full listing data from MongoDB
    3. Attach match_score, is_favorited, units
    4. Save search history (only if results > 0)
    5. Return all results (frontend handles pagination/filtering)
    """
    # Clamp top_k
    top_k = max(1, min(top_k, 100))

    # Query Pinecone
    results = query_records(query, ns="main", top_k=top_k)

    # Extract listing_ids and scores from hits
    hits = results.get("result", {}).get("hits", [])
    hit_map = {}
    for hit in hits:
        lid = hit.get("fields", {}).get("listing_id")
        if lid:
            hit_map[lid] = hit.get("_score", 0)

    if not hit_map:
        return {"listings": [], "total": 0}

    # Fetch full listings from MongoDB
    listings_collection = get_listings_collection()
    mongo_listings = list(listings_collection.find(
        {"listing_id": {"$in": list(hit_map.keys())}},
        {"_id": 0},
    ))

    # Get user favorites
    profile = get_profile_by_user_id(user_id)
    favorites_set = set()
    if profile:
        favorites_set = set(profile.get("favorites", []))

    # Attach scores, favorites, sort by score
    for listing in mongo_listings:
        listing["match_score"] = hit_map.get(listing["listing_id"], 0)
        listing["is_favorited"] = listing["listing_id"] in favorites_set

    mongo_listings.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # Attach units
    _attach_units(mongo_listings)

    total = len(mongo_listings)

    # Save search history (only if results > 0)
    if total > 0:
        _save_search_history(user_id, query, mongo_listings)

    return {"listings": mongo_listings, "total": total}


def _save_search_history(user_id: str, query: str, listings: list) -> None:
    """Save a search to history."""
    try:
        collection = get_search_history_collection()
        collection.insert_one({
            "user_id": user_id,
            "query": query,
            "result_listing_ids": [l["listing_id"] for l in listings],
            "result_count": len(listings),
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning("Failed to save search history: %s", e)


def get_recent_searches(user_id: str, limit: int = 10) -> list:
    """Get recent search history for a user."""
    collection = get_search_history_collection()
    cursor = collection.find(
        {"user_id": user_id},
        {"_id": 0, "query": 1, "result_count": 1, "created_at": 1},
    ).sort("created_at", -1).limit(limit)

    results = []
    for doc in cursor:
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        results.append(doc)
    return results
