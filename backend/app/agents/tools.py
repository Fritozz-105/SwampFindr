"""All tools for the agent"""
import json
import pandas as pd
import numpy as np

from langchain_core.tools import tool
from app.services.pinecone_service import query_records


_bus_stops_df = pd.read_csv('gnv-bus-stops.csv')  # load once


def get_tools():
    """Return a list of all the tools available"""
    return [semantic_search, closest_bus_stops]


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
    lat2_rad = np.radians(df['stop_lat'])
    dlat = lat2_rad - lat1_rad
    dlng = np.radians(df['stop_lon'] - lng)

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

