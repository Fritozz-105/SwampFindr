"""All tools for the agent"""
import json
import pandas as pd
import numpy as np
import httpx
import os 

from langchain_core.tools import tool
from deepeval.tracing import observe
from app.services.pinecone_service import query_records
from app.services.profile_service import PreferencesUpdateRequest, update_preferences, get_profile_by_user_id
from app.database import get_listings_collection, get_units_collection
from app.agents.user_context import get_current_user_id

from pathlib import Path

from openai import OpenAI
from typing import cast
from openai.types.chat import ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONObject


_bus_stops_df = pd.read_csv(Path(__file__).parent / 'gnv-bus-stops.csv')
MAX_SUGGEST_TOP_K = 20
MAX_BUS_RADIUS_M = 10_000

_openai_client = None


def _get_openai_client():
    if _openai_client is not None:
        return _openai_client

    else:
        try:
            return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except Exception as e:
            return f"Could not connect to OpenAI {e}"


def _require_user_id() -> str:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("Authenticated user context is missing")
    return user_id



def get_tools():
    """Return a list of all the tools available"""
    return [
        semantic_search,
        render_listing_cards,
        closest_bus_stops,
        decode_coordinates,
        resolve_destination,
        update_preference_embedding,
        swipe_on_listing,
        suggest_listing,
        get_crimes_nearby,
        get_distance_to_location,
        get_distances_batch,
        get_contact_info
    ]


@tool
@observe(type="tool")
def render_listing_cards(listing_ids: list[str]) -> dict:
    """
    Convert listing IDs into full listing objects so the chat UI can render interactive listing cards.
    Args:
        listing_ids: Ordered list of listing IDs to render.
    Returns:
        JSON string with success/listings/count or an error payload.
    """
    if not isinstance(listing_ids, list) or not listing_ids:
        return json.dumps({"success": False, "error": "listing_ids must be a non-empty list"})

    ordered_ids: list[str] = []
    seen: set[str] = set()
    for raw_id in listing_ids:
        if raw_id is None:
            continue
        lid = str(raw_id).strip()
        if not lid or lid in seen:
            continue
        seen.add(lid)
        ordered_ids.append(lid)

    if not ordered_ids:
        return json.dumps({"success": False, "error": "No valid listing IDs provided"})

    try:
        listings_col = get_listings_collection()
        units_col = get_units_collection()

        listing_docs = {
            doc["listing_id"]: doc
            for doc in listings_col.find({"listing_id": {"$in": ordered_ids}})
        }
        units_by_listing: dict[str, list] = {}
        for unit in units_col.find({"listing_id": {"$in": ordered_ids}}):
            unit["_id"] = str(unit["_id"])
            units_by_listing.setdefault(unit["listing_id"], []).append(unit)

        listings: list[dict] = []
        for listing_id in ordered_ids:
            listing = listing_docs.get(listing_id)
            if not listing:
                continue
            listing["_id"] = str(listing["_id"])
            listing["units"] = units_by_listing.get(listing_id, [])
            listings.append(listing)

        if not listings:
            return json.dumps({"success": False, "error": "No listings found for provided IDs"})

        return json.dumps({"success": True, "listings": listings, "count": len(listings)}, default=str)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("render_listing_cards error: %s", e, exc_info=True)
        return json.dumps({"success": False, "error": "Failed to render listing cards"})


@tool
@observe(type="tool")
def get_contact_info(query: str) -> dict:
    """
    Query the apartment contact information & return it in JSON format
    Accepts natural language queries like 'Get contact info for Sunset Apartments'.
    Args:
        query: The apartment details like "On20 apartments on 20th ave"
    Returns:
        dict: Result with the apartment information in JSON format
    """
    messages = cast(list[ChatCompletionMessageParam], cast(object, [
        {"role": "system",
         "content": """You are a helpful assistant that returns apartment contact information strictly as JSON.
         Always respond with valid JSON only — no extra text, no markdown.
         Format:
        {
            "apartment_name": "...",
            "address": "...",
            "phone": "...",
            "email": "...",
            "website": "...",
            "office_hours": "..."
        }
        If not found, return: {"error": "Apartment not found", "query": "<original query>"}"""
         },
        {"role": "user",
         "content": f"Get contact info for: {query}"
         }
    ]))
    response = _get_openai_client().chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=ResponseFormatJSONObject(type="json_object")
    )

    raw = response.choices[0].message.content
    return json.loads(raw)




@tool
@observe(type="tool")
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

        hit_ids = [h["fields"].get("listing_id") for h in hits if h["fields"].get("listing_id")]
        score_map = {h["fields"].get("listing_id"): h["_score"] for h in hits}

        listings_docs = {doc["listing_id"]: doc for doc in listings_col.find({"listing_id": {"$in": hit_ids}})}
        units_by_listing: dict[str, list] = {}
        for u in units_col.find({"listing_id": {"$in": hit_ids}}):
            u["_id"] = str(u["_id"])
            units_by_listing.setdefault(u["listing_id"], []).append(u)

        listings = []
        for lid in hit_ids:
            listing = listings_docs.get(lid)
            if not listing:
                continue
            listing["_id"] = str(listing["_id"])
            listing["units"] = units_by_listing.get(lid, [])
            listing["match_score"] = score_map.get(lid, 0)
            listings.append(listing)

        return json.dumps({"success": True, "listings": listings, "count": len(listings)}, default=str)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("suggest_listing error: %s", e, exc_info=True)
        return json.dumps({"success": False, "error": "Failed to fetch listing suggestions"})


@tool
@observe(type="tool")
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
        import logging
        logging.getLogger(__name__).error("update_preference_embedding error: %s", e, exc_info=True)
        return {"success": False, "error": "Failed to update preferences"}


@tool
@observe(type="tool")
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
            bedrooms=existing_prefs.get("bedrooms", 1),
            bathrooms=existing_prefs.get("bathrooms", 1),
            price_min=existing_prefs.get("price_min", 500),
            price_max=existing_prefs.get("price_max", 2000),
            distance_from_campus=existing_prefs.get("distance_from_campus", "any"),
            roommates=existing_prefs.get("roommates", 0),
            amenities=existing_prefs.get("amenities", []),
            excerpt=new_excerpt,
        )

        update_preferences(user_id, data)
        return {"success" : True, "excerpt": new_excerpt}

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("swipe_on_listing error: %s", e, exc_info=True)
        return {"success": False, "error": "Failed to record swipe action"}


@tool
@observe(type="tool")
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
@observe(type="tool")
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
    except httpx.HTTPStatusError:
        return {"success": False, "error": "Crime data API returned an error"}
    except Exception:
        return {"success": False, "error": "Failed to fetch crime data"}

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
@observe(type="tool")
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

    except Exception:
        return {"success": False, "error": "Failed to geocode location"}

    return {"success": True, "lat": center_lat, "lng": center_lon}


@tool
@observe(type="tool")
def resolve_destination(placeholder: str, location_bias: str = None) -> dict:
    """
    Resolve a general place name (like 'Walmart') to a specific location using Google Places API.
    This is called when the destination doesn't appear to be a full address (no street number).
    Args:
        placeholder: The destination name/place query (e.g., 'Walmart', 'Marston Library')
        location_bias: Optional location bias for results (e.g., apartment address) to prefer
            nearby results
    Returns:
        Dict with resolved place details (formatted_address) or error
    """
    if not placeholder or not placeholder.strip():
        return {"success": False, "error": "Placeholder is required"}

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY environment variable."
        }

    user_agent = "SwampFindr/1.0 University of Florida (ufl.edu)"
    BASE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

    params = {
        "input": placeholder.strip(),
        "inputtype": "textquery",
        "fields": "formatted_address,geometry/location/lat,geometry/location/lng,name,types",
        "key": api_key,
    }

    # Add location bias if provided
    if location_bias and location_bias.strip():
        params["locationbias"] = f"radius:{location_bias}"

    headers = {"User-Agent": user_agent}

    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            find_resp = client.get(BASE_URL, params=params)
            find_resp.raise_for_status()
            find_data = find_resp.json()

    except httpx.ConnectTimeout:
        return {"success": False, "error": "Connection timed out reaching Google Places API"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Places API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}

    # Check for API errors
    if find_data.get("status") != "OK" or not find_data.get("candidates"):
        return {
            "success": False,
            "error": f"Google Places API found no results for '{placeholder}'",
        }

    # Get the first (most relevant) candidate
    candidate = find_data["candidates"][0]
    formatted_address = candidate.get("formatted_address", placeholder)
    lat = candidate.get("geometry", {}).get("location", {}).get("lat", "")
    lng = candidate.get("geometry", {}).get("location", {}).get("lng", "")

    return {
        "success": True,
        "placeholder": placeholder.strip(),
        "formatted_address": formatted_address,
        "lat": lat,
        "lng": lng,
        "name": candidate.get("name", ""),
    }


@tool
@observe(type="tool")
def get_distances_batch(origins: list[str], destination: str, mode: str = "driving") -> dict:
    """
    Calculate distances from multiple origins to the same destination in a single API call.
    This is useful for showing distances from multiple apartments to the same destination
    (e.g., Walmart). Uses N:1 routing (multiple origins, single destination).
    Args:
        origins: List of origin addresses (apartments). Each will be resolved if needed.
        destination: Single destination address/place name
        mode: Travel mode - 'driving', 'transit', 'walking', or 'bicycling' (default 'driving')
    Returns:
        Dict with individual distance results for each origin-destination pair, or error
    """
    if not origins or not isinstance(origins, list) or len(origins) == 0:
        return {"success": False, "error": "Origins list must contain at least one address"}

    if not destination or not destination.strip():
        return {"success": False, "error": "Destination is required"}

    # Validate mode
    valid_modes = ["driving", "transit", "walking", "bicycling"]
    if mode.lower() not in valid_modes:
        return {
            "success": False,
            "error": f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
        }

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY environment variable."
        }

    user_agent = "SwampFindr/1.0 University of Florida (ufl.edu)"
    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Process origins - pipe-separate for batch query
    origins_str = ", ".join(origin.strip() for origin in origins)

    params = {
        "origins": origins_str,
        "destinations": destination.strip(),
        "mode": mode.lower(),
        "key": api_key,
        "units": "metric",
    }

    headers = {"User-Agent": user_agent}

    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

    except httpx.ConnectTimeout:
        return {"success": False, "error": "Connection timed out reaching Google Maps Distance Matrix API"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}

    # Check for API errors
    if data.get("status") != "OK":
        error_message = data.get("error_message", "Unknown error")
        return {"success": False, "error": f"Google Maps API error: {error_message}"}

    # Extract results for each origin-destination pair
    results = []
    rows = data.get("rows", [])
    dest_addresses = data.get("destination_addresses", [])

    for idx, row in enumerate(rows):
        elements = row.get("elements", [])
        origin = origins[idx] if idx < len(origins) else ""
        dest = dest_addresses[idx] if idx < len(dest_addresses) else destination.strip()

        element = elements[0] if elements else None

        if element and element.get("status") == "OK":
            distance_m = element.get("distance", {}).get("value", 0)
            duration_s = element.get("duration", {}).get("value", 0)

            results.append({
                "origin": origin,
                "destination": dest,
                "distance_km": round(distance_m / 1000, 2),
                "distance_miles": round(distance_m / 1000 * 0.621371, 2),
                "duration_minutes": round(duration_s / 60, 0),
                "duration_formatted": f"{int(duration_s / 60)}m" if duration_s < 3600 else f"{int(duration_s / 3600)}h {int(duration_s % 3600 / 60)}m",
                "status": "OK",
            })
        else:
            results.append({
                "origin": origin,
                "destination": dest,
                "status": element.get("status", "UNKNOWN") if element else "UNKNOWN",
                "error": element.get("errors", ["No route found"])[0].get("message", "No route found") if element else "No route found",
            })

    # If all results failed, return summary
    if not any(r.get("status") == "OK" for r in results):
        return {
            "success": False,
            "error": "No routes found for any origin-destination pair",
            "results": results,
        }

    return {
        "success": True,
        "origin_count": len(results),
        "results": results,
    }


@tool
@observe(type="tool")
def get_distance_to_location(apartment_address: str, destination: str, mode: str = "driving") -> dict:
    """
    Calculate the distance and travel time between an apartment and a destination.
    Call this when the user asks how far an apartment is from a location (e.g., Walmart, campus, etc.)
    For general place names (without street numbers), it first resolves the destination using
    Google Places API before calculating distance.
    Args:
        apartment_address: The full address of the apartment (should include street number)
        destination: The destination (full address or place name like "Walmart" or "Marston Library")
        mode: Travel mode - 'driving', 'transit', 'walking', or 'bicycling' (default 'driving')
    Returns:
        Dict with distance/time values plus resolved addresses from Google, or an error
    """

    # Validate mode
    valid_modes = ["driving", "transit", "walking", "bicycling"]
    if mode.lower() not in valid_modes:
        return {
            "success": False,
            "error": f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
        }

    # Validate addresses
    if not apartment_address or not apartment_address.strip():
        return {"success": False, "error": "Apartment address is required"}
    if not destination or not destination.strip():
        return {"success": False, "error": "Destination is required"}

    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY environment variable."
        }

    user_agent = "SwampFindr/1.0 University of Florida (ufl.edu)"
    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    PLACES_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

    # Detect if destination looks like a general place name (no street number pattern)
    # Pattern: word followed by optional common modifiers (avenue, street, etc.) but no digits
    import re

    destination_lower = destination.lower().strip()
    # Check for street number pattern (digit followed by street type)
    has_street_number = bool(re.search(r'\d+\s*(st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|ln|lane|terrace|way|circle|pl|place|court|driveway|cliff|trail)', destination_lower))
    has_full_address = bool(re.search(r'[a-z]+\s*\d+', destination_lower)) and len(destination) > 20

    # If destination doesn't have a clear street number, try to resolve it first
    if not has_street_number and not has_full_address:
        # Try to resolve the destination using Places API with location bias
        resolution_result = resolve_destination.invoke({
            "placeholder": destination.strip(),
            "location_bias": apartment_address.strip()
        })

        if not resolution_result.get("success"):
            # Fallback to Nominatim geocoding if Places API fails
            return _geocode_with_nominatim_fallback(destination.strip(), mode, apartment_address.strip())

        # Use the resolved address from Places API
        destination = resolution_result.get("formatted_address", destination)
        resolution_success = True
    else:
        resolution_success = None

    # Make Distance Matrix API call
    params = {
        "origins": apartment_address.strip(),
        "destinations": destination.strip(),
        "mode": mode.lower(),
        "key": api_key,
        "units": "metric",  # Return distances in kilometers
    }

    headers = {"User-Agent": user_agent}

    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

    except httpx.ConnectTimeout:
        return {"success": False, "error": "Connection timed out reaching Google Maps API"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}

    # Check for API errors
    if data.get("status") != "OK":
        error_message = data.get("error_message", "Unknown error")
        # If resolution failed earlier, try Nominatim fallback
        if resolution_success is False:
            return _geocode_with_nominatim_fallback(destination.strip(), mode, apartment_address.strip())
        return {"success": False, "error": f"Google Maps API error: {error_message}"}

    # Extract distance and duration from response
    try:
        rows = data.get("rows", [])
        if not rows or not rows[0].get("elements"):
            return {"success": False, "error": "No route found between the two locations"}

        element = rows[0]["elements"][0]

        # Check if route is possible
        if element.get("status") != "OK":
            return {"success": False, "error": f"Route not found: {element.get('status', 'UNKNOWN')}"}

        resolved_apartment_address = (data.get("origin_addresses") or [apartment_address.strip()])[0]
        resolved_destination = (data.get("destination_addresses") or [destination.strip()])[0]

        distance_m = element.get("distance", {}).get("value", 0)
        duration_s = element.get("duration", {}).get("value", 0)

        # Convert to user-friendly units
        distance_km = distance_m / 1000
        distance_miles = distance_km * 0.621371
        duration_minutes = duration_s / 60
        duration_hours = duration_minutes / 60

        return {
            "success": True,
            "apartment_address": apartment_address.strip(),
            "destination": destination.strip(),
            "resolved_apartment_address": resolved_apartment_address,
            "resolved_destination": resolved_destination,
            "mode": mode.lower(),
            "distance_km": round(distance_km, 2),
            "distance_miles": round(distance_miles, 2),
            "duration_minutes": round(duration_minutes, 0),
            "duration_hours": round(duration_hours, 1),
            "duration_formatted": f"{int(duration_hours)}h {int(duration_minutes % 60)}m" if duration_hours >= 1 else f"{int(duration_minutes)}m"
        }
    except KeyError as e:
        return {"success": False, "error": f"Unexpected API response format: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing response: {str(e)}"}


def _geocode_with_nominatim_fallback(destination: str, mode: str, apartment_address: str) -> dict:
    """
    Fallback geocoding using Nominatim OpenStreetMap when Google Places API fails.
    This allows the tool to still work even if Google API quota is exhausted.
    """
    BASE_URL = "https://nominatim.openstreetmap.org/search"

    user_agent = "SwampFindr/1.0 University of Florida (ufl.edu)"

    params = {
        "q": destination,
        "format": "jsonv2",
        "limit": 3,
        "addressdetails": 1,
    }

    try:
        with httpx.Client(timeout=15.0, headers={"User-Agent": user_agent}) as client:
            geocode_resp = client.get(BASE_URL, params=params)
            geocode_resp.raise_for_status()
            geocode_data = geocode_resp.json()
    except Exception as e:
        return {"success": False, "error": f"Nominatim geocoding failed: {e}"}

    if not geocode_data:
        return {
            "success": False,
            "error": f"Could not resolve destination '{destination}' - not found in Google Places or Nominatim"
        }

    # Use the closest result (may need additional refinement)
    first_result = geocode_data[0]
    fallback_address = f"{first_result.get('display_name', destination)}, {apartment_address}"

    # Make distance matrix call with fallback address
    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if not api_key:
        return {"success": False, "error": "Nominatim geocoding succeeded but Google Maps API key not configured"}

    params = {
        "origins": apartment_address.strip(),
        "destinations": fallback_address,
        "mode": mode.lower(),
        "key": api_key,
        "units": "metric",
    }

    try:
        with httpx.Client(timeout=10.0, headers={"User-Agent": user_agent}) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectTimeout:
        return {"success": False, "error": "Connection timed out reaching Google Maps API"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}

    # Check for API errors
    if data.get("status") != "OK":
        error_message = data.get("error_message", "Unknown error")
        return {"success": False, "error": f"Google Maps API error: {error_message}"}

    try:
        rows = data.get("rows", [])
        if not rows or not rows[0].get("elements"):
            return {"success": False, "error": "No route found between the locations"}

        element = rows[0]["elements"][0]

        if element.get("status") != "OK":
            return {"success": False, "error": f"Route not found: {element.get('status', 'UNKNOWN')}"}

        distance_m = element.get("distance", {}).get("value", 0)
        duration_s = element.get("duration", {}).get("value", 0)

        distance_km = distance_m / 1000
        distance_miles = distance_km * 0.621371
        duration_minutes = duration_s / 60
        duration_hours = duration_minutes / 60

        return {
            "success": True,
            "apartment_address": apartment_address.strip(),
            "destination": destination,
            "resolved_destination": fallback_address,
            "mode": mode.lower(),
            "distance_km": round(distance_km, 2),
            "distance_miles": round(distance_miles, 2),
            "duration_minutes": round(duration_minutes, 0),
            "duration_hours": round(duration_hours, 1),
            "duration_formatted": f"{int(duration_hours)}h {int(duration_minutes % 60)}m" if duration_hours >= 1 else f"{int(duration_minutes)}m",
            "resolved_via": "Nominatim fallback",
        }
    except KeyError as e:
        return {"success": False, "error": f"Unexpected API response format: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing Nominatim fallback: {str(e)}"}


@tool
@observe(type="tool")
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
