"""Recommendation service."""
import logging
from typing import Optional

from app.database import get_listings_collection
from app.services.listing_utils import attach_units
from app.services.profile_service import get_profile_by_user_id, get_favorites
from app.services.pinecone_service import query_records

logger = logging.getLogger(__name__)


def _build_preference_query(prefs: dict) -> str:
  """Build a natural-language query from user preferences for Pinecone search."""
  parts = [
    f"Looking for a place with {prefs.get('bedrooms', 1)} bedroom(s)",
    f"and {prefs.get('bathrooms', 1)} bathroom(s).",
    f"Budget: ${prefs.get('price_min', 500)} to ${prefs.get('price_max', 2000)} per month.",
  ]

  distance = prefs.get("distance_from_campus", "any")
  if distance != "any":
    parts.append(f"Preferred distance from campus: {distance}.")

  roommates = prefs.get("roommates", 0)
  if roommates > 0:
    parts.append(f"Open to {roommates} roommate(s).")

  amenities = prefs.get("amenities", [])
  if amenities:
    parts.append(f"Must-have amenities: {', '.join(amenities)}.")

  excerpt = prefs.get("excerpt", "")
  if excerpt:
    parts.append(f"Additional notes: {excerpt}")

  return " ".join(parts)


def get_recommendations(user_id: str, page: int, per_page: int) -> dict:
  """
  Get personalized listing recommendations for a user.

  Tries Pinecone vector similarity first, falls back to MongoDB query matching.
  """
  profile = get_profile_by_user_id(user_id)
  if not profile:
    return {"listings": [], "pagination": _pagination(page, per_page, 0), "source": "fallback"}

  prefs = profile.get("preferences", {})
  favorites = profile.get("favorites", [])
  favorites_set = set(favorites)

  source = "pinecone"
  listings = []

  try:
    query_text = _build_preference_query(prefs)
    # Fetch enough results to paginate from
    total_needed = page * per_page
    results = query_records(query_text, ns="main", top_k=total_needed)

    # Extract listing_ids and scores from Pinecone hits
    hits = results.get("result", {}).get("hits", [])
    if not hits:
      raise ValueError("No Pinecone hits returned")

    hit_map = {}
    for hit in hits:
      lid = hit.get("fields", {}).get("listing_id")
      if lid:
        hit_map[lid] = hit.get("_score", 0)

    if not hit_map:
      raise ValueError("No listing_ids in Pinecone hits")

    # Fetch listings from MongoDB
    listings_collection = get_listings_collection()
    mongo_listings = list(listings_collection.find(
      {"listing_id": {"$in": list(hit_map.keys())}},
      {"_id": 0},
    ))

    # Attach match scores and sort by score descending
    for listing in mongo_listings:
      listing["match_score"] = hit_map.get(listing["listing_id"], 0)
      listing["is_favorited"] = listing["listing_id"] in favorites_set

    mongo_listings.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # Paginate
    total = len(mongo_listings)
    start = (page - 1) * per_page
    listings = mongo_listings[start:start + per_page]

  except Exception as e:
    logger.warning("Pinecone unavailable, falling back to MongoDB: %s", e)
    source = "fallback"
    listings, total = _fallback_recommendations(prefs, favorites_set, page, per_page)

  attach_units(listings)

  return {
    "listings": listings,
    "pagination": _pagination(page, per_page, total),
    "source": source,
  }


def _fallback_recommendations(
  prefs: dict,
  favorites_set: set,
  page: int,
  per_page: int,
) -> tuple:
  """MongoDB fallback: query listings matching user preferences."""
  listings_collection = get_listings_collection()

  query = {}
  price_min = prefs.get("price_min")
  price_max = prefs.get("price_max")
  if price_min is not None and price_max is not None:
    query["list_price_min"] = {"$lte": price_max}
    query["list_price_max"] = {"$gte": price_min}

  beds = prefs.get("bedrooms")
  if beds is not None and beds > 0:
    query["beds_min"] = {"$lte": beds}
    query["beds_max"] = {"$gte": beds}

  total = listings_collection.count_documents(query)
  skip = (page - 1) * per_page

  cursor = (
    listings_collection
    .find(query, {"_id": 0})
    .sort("list_price_min", 1)
    .skip(skip)
    .limit(per_page)
  )

  listings = []
  for listing in cursor:
    listing["match_score"] = None
    listing["is_favorited"] = listing["listing_id"] in favorites_set
    listings.append(listing)

  return listings, total


def _pagination(page: int, per_page: int, total: int) -> dict:
  """Build pagination metadata."""
  return {
    "page": page,
    "per_page": per_page,
    "total": total,
    "has_next": (page * per_page) < total,
  }
