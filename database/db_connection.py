import asyncio

from backend.config import settings
from database.postgres_client import get_postgres_client
from database.qdrant_client import get_qdrant_client
from services.mcp_client import health_check as mcp_health_check


def health_check() -> dict:
    if settings.USE_MCP:
        try:
            gateway = asyncio.run(mcp_health_check())
            checks = (gateway.get("data") or {}).get("checks", {}) if isinstance(gateway, dict) else {}
            return {
                "postgres": "ok" if checks.get("postgres") == "ok" else "error",
                "qdrant": "ok" if checks.get("qdrant") == "ok" else "error",
            }
        except RuntimeError:
            # Avoid nested event-loop crashes; route-level async health checks handle MCP details.
            return {"postgres": "unknown", "qdrant": "unknown"}

    postgres = get_postgres_client()
    qdrant = get_qdrant_client()
    return {
        "postgres": postgres.get("status", "unknown"),
        "qdrant": qdrant.get("status", "unknown"),
    }
