"""All tools for the agent"""
from langchain_core.tools import tool
from app.services.pinecone_service import query_records


def get_tools():
    return [semantic_search]


@tool
def semantic_search(query: str):
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

