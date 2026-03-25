import os
import uuid
from threading import Lock
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "main-vector-db"


pc = None
idx = None
_init_lock = Lock()

_NAMESPACE_ALIASES = {
    'user_preference' : 'user-preferences',
    'user_preferences' : 'user-preferences',
}

_ALLOWED_NAMESPACES = {"main", "user-preferences", "test"}

def _norm_ns(ns: str) -> str:
    if not ns:
        raise ValueError('Namespace required...')
    norm = _NAMESPACE_ALIASES.get(ns, ns)
    if norm not in _ALLOWED_NAMESPACES:
        raise ValueError('Unsupported namespace: {}'.format(norm))
    return norm


def _get_idx():
    global pc, idx
    if idx is not None:
        return idx
    with _init_lock:
        if idx is not None:
            return idx
        if not PINECONE_API_KEY:
            raise ValueError('Pinecone API key not provided...')
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(INDEX_NAME)
        return idx


def pc_health():
    try:
        stats = _get_idx().describe_index_stats()
        return {'ok': True, 'index': INDEX_NAME, 'stats': stats}
    except Exception as e:
        return {'ok': False, 'index': INDEX_NAME ,'error': str(e)}


def upsert_record(chunk_text, category, ns='main', user_id=None, listing_id=None):
    namespace = _norm_ns(ns)
    record_id = f"ID-{user_id}" if user_id else f"ID-{listing_id}" if listing_id else f"ID-{uuid.uuid4()}"
    _get_idx().upsert_records(
        namespace,
        [
            {
                "_id": record_id,
                "chunk_text": chunk_text,
                "category": category,
                **({"user_id": user_id} if user_id else {}),
                **({"listing_id": listing_id} if listing_id else {}),
            }
        ]
    )
    return record_id


def query_records(query_text, ns, top_k=3):
    namespace = _norm_ns(ns)
    results = _get_idx().search(
        namespace,
        {
            "inputs": {"text": query_text},
            "top_k": top_k
        },
        fields=["chunk_text", "category", "listing_id", "latitude", "longitude"]
    )
    return results
