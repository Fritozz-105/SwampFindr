import os
import uuid
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "main-vector-db"


pc = Pinecone(api_key=PINECONE_API_KEY)
idx = pc.Index(INDEX_NAME)


def upsert_record(chunk_text, category, ns='main', user_id=None, listing_id=None):
    record_id = f"user-{user_id}" if user_id else str(uuid.uuid4())
    idx.upsert_records(
        ns,
        [
            {
                "_id": record_id,
                "chunk_text": chunk_text,
                "category": category,
                **({"user_id": user_id} if user_id else {}),
                **{{"listing_id": listing_id} if listing_id else {}},
            }
        ]
    )
    return record_id


def query_records(query_text, ns, top_k=3):
    results = idx.search(
        ns,
        {
            "inputs": {"text": query_text},
            "top_k": top_k
        },
        fields=["chunk_text", "category"]
    )
    return results
