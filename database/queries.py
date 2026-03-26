from backend.config import settings
from database.postgres_client import search_knowledge_chunks
from services.mcp_client import call_tool


def fetch_threat_indicators(indicator: str) -> dict:
    return {"indicator": indicator, "matches": []}


async def fetch_rag_matches(query_vector: list[float], limit: int | None = None) -> dict:
    if settings.USE_MCP:
        response = await call_tool(
            "pg_query",
            {
                "query_id": "knowledge_similarity_search",
                "params": {
                    "vector": query_vector,
                    "limit": limit or settings.RAG_TOP_K,
                    "min_similarity": settings.RAG_MIN_SIMILARITY,
                    "table_name": settings.RAG_VECTOR_TABLE,
                },
            },
        )
        if response.get("status") != "ok":
            return {
                "status": response.get("status", "error"),
                "matches": [],
                "reason": response.get("reason", "MCP pg_query failed."),
            }

        rows = (response.get("data") or {}).get("rows", [])
        matches: list[dict] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            matches.append(
                {
                    "id": row.get("id") or row.get("chunk_id"),
                    "source": row.get("source", "shaktidb"),
                    "text": row.get("text") or row.get("chunk") or row.get("chunk_text") or "",
                    "metadata": row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
                    "similarity": float(row.get("similarity", row.get("score", 0.0))),
                }
            )
        return {"status": "ok", "matches": matches}

    return search_knowledge_chunks(
        query_vector,
        table_name=settings.RAG_VECTOR_TABLE,
        limit=limit or settings.RAG_TOP_K,
        min_similarity=settings.RAG_MIN_SIMILARITY,
    )
