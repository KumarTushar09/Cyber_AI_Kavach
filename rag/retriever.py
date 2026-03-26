from backend.config import settings
from database.queries import fetch_rag_matches
from services.embedding_service import embed_text


def _chunk_query(query: str) -> list[str]:
    size = max(32, settings.RAG_QUERY_CHUNK_SIZE)
    overlap = max(0, min(settings.RAG_QUERY_CHUNK_OVERLAP, size - 1))
    step = size - overlap if size > overlap else size

    normalized = " ".join(query.split())
    if len(normalized) <= size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        chunks.append(normalized[start : start + size])
        start += step
    return chunks


async def retrieve(query: str) -> list[dict]:
    query_chunks = _chunk_query(query)
    ranked: dict[str, dict] = {}

    for part in query_chunks:
        embedding = await embed_text(part)
        db_result = await fetch_rag_matches(embedding, limit=settings.RAG_TOP_K)
        matches = db_result.get("matches", []) if isinstance(db_result, dict) else []

        for match in matches:
            key = str(match.get("id") or f"{match.get('source')}::{match.get('text')}")
            prev = ranked.get(key)
            score = float(match.get("similarity", 0.0))
            if not prev or score > float(prev.get("similarity", 0.0)):
                ranked[key] = {
                    "id": match.get("id"),
                    "source": match.get("source", "shaktidb"),
                    "text": match.get("text", ""),
                    "metadata": match.get("metadata", {}),
                    "similarity": score,
                }

    chunks = sorted(ranked.values(), key=lambda item: float(item.get("similarity", 0.0)), reverse=True)
    if not chunks:
        return [{"source": "shaktidb", "text": f"No indexed docs found for: {query}", "similarity": 0.0}]
    return chunks[: settings.RAG_TOP_K]
