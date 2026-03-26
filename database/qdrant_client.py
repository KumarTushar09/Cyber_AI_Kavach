import os
from typing import Any

try:
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover - optional at edit time
    QdrantClient = None


def _build_client() -> Any:
    host = os.getenv("QDRANT_HOST", "").strip()
    port = int(os.getenv("QDRANT_PORT", "6333"))
    if not host or QdrantClient is None:
        return None
    return QdrantClient(host=host, port=port)


def get_qdrant_client() -> dict[str, Any]:
    if QdrantClient is None:
        return {"status": "error", "message": "qdrant-client is not installed in this runtime."}
    client = _build_client()
    if client is None:
        return {"status": "skipped", "message": "Qdrant env is not configured yet."}
    try:
        collections = client.get_collections()
        return {
            "status": "ok",
            "message": "Qdrant connection succeeded.",
            "collections": len(getattr(collections, "collections", [])),
        }
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "message": str(exc)}


def search_threat_vectors(vector: list[float], limit: int = 5) -> dict[str, Any]:
    collection = os.getenv("QDRANT_COLLECTION_THREATS", "threat_vectors")
    client = _build_client()
    if client is None:
        return {"status": "skipped", "matches": [], "reason": "Qdrant is not configured yet."}
    try:
        hits = client.search(collection_name=collection, query_vector=vector, limit=limit)
        matches = [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in hits
        ]
        return {"status": "ok", "matches": matches}
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "matches": [], "reason": str(exc)}
