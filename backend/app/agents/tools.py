"""All tools for the agent"""
import json
import pandas as pd
import numpy as np

from langchain_core.tools import tool
from app.services.pinecone_service import query_records
from app.services.profile_service import PreferencesUpdateRequest, update_preferences, get_profile_by_user_id
from app.database import get_listings_collection, get_units_collection

from pathlib import Path


_bus_stops_df = pd.read_csv(Path(__file__).parent / 'gnv-bus-stops.csv')


def get_tools():
    """Return a list of all the tools available"""
    return [semantic_search, closest_bus_stops, update_preference_embedding, swipe_on_listing]


@tool 
def update_preference_embedding(
        user_id: str,
        bedrooms: int = 1,
        bathrooms: int = 1,
        price_min: int = 500,
        price_max: int = 1800,
        distance_from_campus: str = "any",
        roommates: int = 0,
        amenities: list[str] = [],
        excerpt: str = ""
)-> dict:
    """Update the user's housing preferences and recompile their preferences embedding.
    This should be called when the user implicitly or directly expresses a change in interest
    Args:
        user_id: User ID
        bedrooms: Number of bedrooms in each apartment
        bathrooms: Number of bathrooms in each apartment
        price_min: Minimum price in each apartment
        price_max: Maximum price in each apartment
        distance_from_campus: Preferred distance from UF campus
        roommates: Number of roommates in each apartment
        amenities: Amenities in each apartment
        excerpt: Any additional notes to be embedded
    Returns:
        Dict with 'success' and updated profile data or either an 'error'
    """
    try:
        data = PreferencesUpdateRequest(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            price_min=price_min,
            price_max=price_max,
            distance_from_campus=distance_from_campus,
            roommates=roommates,
            amenities=amenities,
            excerpt=excerpt,
        )
        profile = update_preferences(user_id, data)
        if not profile:
            return {
                "success": False,
                "error": "Profile was not found"
            }
        return {
            "success": True,
            "data": profile
        }
    except Exception as e:
        return {"success": False, "error": f"Error with updating preferences | {str(e)}"}


@tool
def swipe_on_listing(user_id: str, listing_id: str, action: str) -> dict:
    """
    Track the user's interest via a swipe on a listing (like/dislike/pass)
    This tool should be called when the user reacts to an apartment and it updates the excerpt in the embedding
    Args:
        user_id: The user's identification key
        listing_id: Listing that the user is reacting to
        action: 'like' 'dislike' 'pass'
    Returns:
        Dictionary with the user's recorded action
    """
    if action.lower() not in ('like', 'dislike', 'pass'):
        return {"success": False, "error": f"Error with parsing user action"}

    try:
        listings = get_listings_collection()
        listing = listings.find_one({'listing_id': listing_id})
        if not listing:
            return {"success": False, "error" : "Listing not found"}

        profile = get_profile_by_user_id(user_id)
        if not profile:
            return {"success": False, "error": "Profile not found"}

        existing_prefs = profile.get('preferences', {})
        existing_excerpt = existing_prefs.get("excerpt", "")

        extension = "ed" if action == "pass" else "d"

        city = listing.get("City") or listing.get("city", "")
        beds = listing.get("beds_min", "?")
        price = listing.get("list_price_min", "?")
        snippet = f"User {action}{extension} a {beds}bd ~${price}/mo in {city}."

        new_excerpt = f"{existing_excerpt} {snippet}"
        new_excerpt = new_excerpt[-250:]

        data = PreferencesUpdateRequest(
            **{k: existing_prefs[k] for k in existing_prefs if k != "excerpt"},
            excerpt=new_excerpt
        )

        update_preferences(user_id, data)
        return {"success" : True, "excerpt": new_excerpt}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def suggest_listing() -> dict:
    """
    Suggest another listing to the user, this action is ideally completed when the user swipes on a listing.
    Args:
        NONE
    Returns:
        Dictionary with the listing details to propose to the user.
    """
    try:
        listings = get_listings_collection()

@tool
def closest_bus_stops(lat: float, lng: float, radius_m: float = 1000) -> dict:
    """
    Find all bus stops within a given radius of a location.
    Args:
        lat: Latitude of the target location
        lng: Longitude of the target location
        radius_m: Search radius in meters (default 1000m)
    Returns:
        Dict with 'stops' (list of nearby bus stops) and 'count' (number of stops found)
    """
    df = _bus_stops_df.copy()
    R = 6_371_000

    lat1_rad = np.radians(lat)
    lat2_rad = np.radians(df['Latitude'])
    dlat = lat2_rad - lat1_rad
    dlng = np.radians(df['Longitude'] - lng)

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlng / 2) ** 2
    df['distance_m'] = R * 2 * np.arcsin(np.sqrt(a))

    results_df = df[df['distance_m'] <= radius_m].sort_values('distance_m').reset_index(drop=True)

    if results_df.empty:
        return {"stops": [], "count": 0, "message": "No bus stops found within the given radius"}

    return {
        "stops": json.loads(results_df.to_json(orient='records')),
        "count": len(results_df)
    }


@tool
def semantic_search(query: str):
    """
    Find k=3 matching vectors from the database that align with the query vector.
    Arguments:
        query (str): The query vector
    Returns:
        List of:
        {"id" : id of vector hit
        "text" : text of vector hit
        "category" : category of vector hit
        "score" : score of vector hit}
    """
    results = query_records(
        query_text = query,
        ns="main",
        top_k=3
    )

    hits = results.get("result", {}).get("hits", [])

    return [
        {
            "id": hit["_id"],
            "text": hit["fields"].get("chunk_text", ""),
            "category": hit["fields"].get("category", ""),
            "score": hit["_score"],
        }
        for hit in hits
    ]