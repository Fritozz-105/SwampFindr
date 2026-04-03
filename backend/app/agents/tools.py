"""All tools for the agent"""
import json
import pandas as pd
import numpy as np
import httpx

from langchain_core.tools import tool
from app.services.pinecone_service import query_records
from app.services.profile_service import PreferencesUpdateRequest, update_preferences, get_profile_by_user_id
from app.database import get_listings_collection, get_units_collection
from app.agents.user_context import get_current_user_id

from pathlib import Path


_bus_stops_df = pd.read_csv(Path(__file__).parent / 'gnv-bus-stops.csv')
MAX_SUGGEST_TOP_K = 20
MAX_BUS_RADIUS_M = 10_000


def _require_user_id() -> str:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("Authenticated user context is missing")
    return user_id


def get_tools():
    """Return a list of all the tools available"""
    return [
        semantic_search,
        closest_bus_stops,
        decode_coordinates,
        update_preference_embedding,
        swipe_on_listing,
        suggest_listing,
        get_crimes_nearby
    ]


@tool
def suggest_listing(top_k: int = 1) -> dict:
    """
       Suggest apartment listings based on the user's  preferences embedding.
       Call this when the user asks for recommendations, suggestions, or wants to find apartments.
       Args:
           top_k: Number of listings to return (default 3)
       Returns:
           Dict with 'listings' (list of matched listings with units) or 'error'
    """
    if top_k < 1 or top_k > MAX_SUGGEST_TOP_K:
        return {
            "success": False,
            "error": f"top_k must be between 1 and {MAX_SUGGEST_TOP_K}",
        }

    user_id = _require_user_id()
    try:
        profile = get_profile_by_user_id(user_id)
        if not profile:
            return {"success": False, "error": "Profile not found"}

        prefs = profile.get("preferences", {})

        query = (
            f"{prefs.get('bedrooms', 1)} bedroom apartment, "
            f"${prefs.get('price_min', 500)}-${prefs.get('price_max', 1800)}/mo, "
            f"distance from campus: {prefs.get('distance_from_campus', 'any')}, "
            f"amenities: {', '.join(prefs.get('amenities', []) or [])}. "
            f"{prefs.get('excerpt', '')}"
        )

        results = query_records(query, ns = "main", top_k=top_k)
        hits = results.get("result", {}).get("hits", [])

        if not hits:
            return {"success": False, "error": "No results"}

        listings_col = get_listings_collection()
        units_col = get_units_collection()

        listings = []
        for hit in hits:
            listing_id = hit["fields"].get("listing_id")
            if not listing_id:
                continue
            listing = listings_col.find_one({"listing_id": listing_id})
            if not listing:
                continue

            listing["_id"] = str(listing["_id"])
            units = list(units_col.find({"listing_id": listing_id}))
            for u in units:
                u["_id"] = str(u["_id"])
            listing["units"] = units
            listing["match_score"] = hit["_score"]
            listings.append(listing)

        return {"success": True, "listings": listings, "count": len(listings)}

    except Exception as e:
        return {"success" :False, "error": str(e)}


@tool
def update_preference_embedding(
        bedrooms: int = 1,
        bathrooms: int = 1,
        price_min: int = 500,
        price_max: int = 1800,
        distance_from_campus: str = "any",
        roommates: int = 0,
        amenities: list[str] | None = None,
        excerpt: str = ""
)-> dict:
    """Update the user's housing preferences and recompile their preferences embedding.
    This should be called when the user implicitly or directly expresses a change in interest
    Args:
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
    user_id = _require_user_id()
    try:
        amenities = amenities or []
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
def swipe_on_listing(listing_id: str, action: str) -> dict:
    """
    Track the user's interest via a swipe on a listing (like/dislike/pass)
    This tool should be called when the user reacts to an apartment and it updates the excerpt in the embedding
    Args:
        listing_id: Listing that the user is reacting to
        action: 'like' 'dislike' 'pass'
    Returns:
        Dictionary with the user's recorded action
    """
    if action.lower() not in ('like', 'dislike', 'pass'):
        return {"success": False, "error": f"Error with parsing user action"}

    user_id = _require_user_id()
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
        new_excerpt = new_excerpt[-200:]

        data = PreferencesUpdateRequest(
            **{k: existing_prefs[k] for k in existing_prefs if k != "excerpt"},
            excerpt=new_excerpt
        )

        update_preferences(user_id, data)
        return {"success" : True, "excerpt": new_excerpt}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def closest_bus_stops(lat: float, lng: float, radius_m: float = 350) -> dict:
    """
    Find all bus stops within a given radius of a location.
    Args:
        lat: Latitude of the target location
        lng: Longitude of the target location
        radius_m: Search radius in meters (default 1000m)
    Returns:
        Dict with 'stops' (list of nearby bus stops) and 'count' (number of stops found)
    """
    if not (-90 <= lat <= 90):
        return {"stops": [], "count": 0, "error": "lat must be between -90 and 90"}
    if not (-180 <= lng <= 180):
        return {"stops": [], "count": 0, "error": "lng must be between -180 and 180"}
    if radius_m <= 0 or radius_m > MAX_BUS_RADIUS_M:
        return {
            "stops": [],
            "count": 0,
            "error": f"radius_m must be > 0 and <= {MAX_BUS_RADIUS_M}",
        }

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
def get_crimes_nearby(lat: float, lng: float, radius_m: float = 800, limit: int = 50) -> dict:
    """
    Fetch recent crime incidents near a given pair of coordinates via the GNV open data portal.
    Args:
        lat: Latitude of the target location
        lng: Longitude of the target location
        radius_m: Search radius in meters (default 800m)
        limit: Maximum # of incidents to return (default 50)

    Returns:
        Dictionary with the 'incidents', 'count', and 'summary'
    """
    if not (-90 <= lat <= 90):
        return {"success": False, "error": "Latitude must be between -90 and 90"}
    if not (-180 <= lng <= 180):
        return {"success": False, "error": "Longitude must be between -180 and 180"}
    if radius_m <= 0 or radius_m > 5000:
        return {"success": False, "error": "radius_m must be between 0 and 5000"}

    limit = max(1, min(limit, 200))
    BASE_URL = "https://data.cityofgainesville.org/resource/gvua-xt9q.json"
    HEADERS = {"User-Agent": "SwampFindr/1.0 University of Florida (ufl.edu)"}

    params = {
        "$where": f"within_circle(location, {lat}, {lng}, {radius_m})",
        "$limit": limit,
        "$order": "report_date DESC",
        "$select": "report_date,offense_date,narrative,address,latitude,longitude",
    }

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectTimeout:
        return {"success": False, "error": "Connection timed out reaching crime data API"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}

    if not data:
        return {"success": True, "incidents": [], "count": 0, "summary": {}}

    summary: dict[str, int] = {}

    incidents = []
    for row in data:
        offense = row.get("narrative") or "Unknown"
        summary[offense] = summary.get(offense, 0) + 1
        incidents.append({
            "date": row.get("report_date", ""),
            "offense": offense,
            "address": row.get("address", ""),
            "lat": row.get("latitude"),
            "lng": row.get("longitude"),
        })

    return {
        "success": True,
        "incidents": incidents,
        "count": len(incidents),
        "summary": dict(sorted(summary.items(), key=lambda x: x[1], reverse=True)),
        "radius_m": radius_m,
        "source": "Gainesville Police Department via dataGNV (data.cityofgainesville.org)",
    }


@tool
def decode_coordinates(location: str) :
    """
    Geocode a location to get its longitude and latitude coordinates
    Args:
        location: A place/address query to geocode
    Returns:
        Data with the latitude and longitude of a given coordinate
    """
    if not location or not location.strip():
        return {"success": False, "error": "Need location!"}

    user_agent = "SwampFindr/1.0 University of Florida (ufl.edu)"

    try:
        with httpx.Client(timeout=15.0, headers={"User-Agent": user_agent}) as client:
            geocode_resp = client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": location.strip(), "format": "jsonv2", "limit": 1},
            )
            geocode_resp.raise_for_status()
            geocode_data = geocode_resp.json()
            if not geocode_data:
                return {
                    "success": False,
                    "error": "No coordinates found for the given location",
                }

            center_lat = float(geocode_data[0]["lat"])
            center_lon = float(geocode_data[0]["lon"])

    except Exception as e:
        return {"success": False, "error": f"Error: {e}"}

    return {"success": True, "lat": center_lat, "lng": center_lon}


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
            "listing_id" : hit["fields"].get("listing_id", "")
        }
        for hit in hits
    ]
