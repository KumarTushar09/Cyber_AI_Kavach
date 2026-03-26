import os
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover - optional at edit time
    psycopg = None


def _dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "5432").strip()
    db = os.getenv("POSTGRES_DB", "").strip()
    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()
    if not (host and db and user and password):
        return ""
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def get_postgres_client() -> dict[str, Any]:
    dsn = _dsn()
    if not dsn:
        return {"status": "skipped", "message": "Postgres env is not configured yet."}
    if psycopg is None:
        return {"status": "error", "message": "psycopg is not installed in this runtime."}
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "ok", "message": "Postgres connection succeeded."}
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "message": str(exc)}


def fetch_indicator_matches(indicator: str, limit: int = 5) -> dict[str, Any]:
    dsn = _dsn()
    if not dsn:
        return {"status": "skipped", "matches": [], "reason": "Postgres env is not configured yet."}
    if psycopg is None:
        return {"status": "error", "matches": [], "reason": "psycopg is not installed in this runtime."}

    query = """
        SELECT indicator, category, confidence
        FROM threat_indicators
        WHERE indicator = %(indicator)s
        ORDER BY confidence DESC
        LIMIT %(limit)s
    """
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"indicator": indicator, "limit": limit})
                rows = cur.fetchall()
        matches = [
            {"indicator": row[0], "category": row[1], "confidence": row[2]}
            for row in rows
        ]
        return {"status": "ok", "matches": matches}
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "matches": [], "reason": str(exc)}


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.10f}" for v in vector) + "]"


def search_knowledge_chunks(
    query_vector: list[float],
    *,
    table_name: str,
    limit: int = 5,
    min_similarity: float = 0.2,
) -> dict[str, Any]:
    dsn = _dsn()
    if not dsn:
        return {"status": "skipped", "matches": [], "reason": "Postgres env is not configured yet."}
    if psycopg is None:
        return {"status": "error", "matches": [], "reason": "psycopg is not installed in this runtime."}
    if not query_vector:
        return {"status": "error", "matches": [], "reason": "query_vector is empty."}

    vector = _vector_literal(query_vector)
    sql = f"""
        SELECT
            id,
            source,
            chunk,
            metadata,
            1 - (embedding <=> %s::vector) AS similarity
        FROM {table_name}
        WHERE 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (vector, vector, min_similarity, vector, limit))
                rows = cur.fetchall()

        matches = [
            {
                "id": row[0],
                "source": row[1],
                "text": row[2],
                "metadata": row[3] if isinstance(row[3], dict) else {},
                "similarity": float(row[4]),
            }
            for row in rows
        ]
        return {"status": "ok", "matches": matches}
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "matches": [], "reason": str(exc)}
