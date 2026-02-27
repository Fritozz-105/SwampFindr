"""All tools for the agent"""
import json
from langchain_core.tools import tool
from backend.app.services.pinecone_service import query_records
import pandas as pd
import numpy as np


def get_tools():
    """Return a list of all the tools available"""
    return [semantic_search, closest_bus_stops]


@tool
def closest_bus_stops(lat: float, lng: float, radius_m: float = 1000):
    """
    Find all bus stops within a given radius of a location.
    Arguments:
        lat (float): Latitude of the target location
        lng (longitude): Longitude of the target location
        radius_m (float): Search radius in meters (default 1000m)

    Returns:
        Tuple of:
        JSON: Nearby bus stops
        int: amount of nearest bus stops
    """
    df = pd.read_csv('gnv-bus-stops.csv')
    R = 6_371_000  # Earth's radius in meters

    lat1 = np.radians(lat)
    lat2 = np.radians(df['stop_lat'])
    dlat = np.radians(df['stop_lat'] - lat)
    dlng = np.radians(df['stop_lon'] - lng)

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    df['distance_m'] = R * 2 * np.arcsin(np.sqrt(a))

    results_df = df[df['distance_m'] <= radius_m].sort_values('distance_m').reset_index(drop=True)
    results_json = results_df.to_json(orient='records')

    return results_json, len(results_df)


@tool
def semantic_search(query: str):
    """Semantic search for relevant apartments in the vector database"""
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

