from backend.config import settings
from services.mcp_client import call_tool
from services.sarvam_service import embed_text_via_sarvam


async def embed_text(text: str) -> list[float]:
    if settings.USE_MCP:
        result = await call_tool("embed", {"text": text})
        if result.get("status") == "ok":
            result = {
                "status": "ok",
                "embedding": (result.get("data") or {}).get("embedding", []),
            }
    else:
        result = await embed_text_via_sarvam(text)

    if result.get("status") != "ok":
        return [0.0] * settings.EMBEDDING_DIMENSION

    vector = result.get("embedding") or []
    if not isinstance(vector, list) or not vector:
        return [0.0] * settings.EMBEDDING_DIMENSION

    # Keep vector shape stable for DB-side similarity operations.
    if len(vector) > settings.EMBEDDING_DIMENSION:
        return [float(v) for v in vector[: settings.EMBEDDING_DIMENSION]]
    if len(vector) < settings.EMBEDDING_DIMENSION:
        padding = [0.0] * (settings.EMBEDDING_DIMENSION - len(vector))
        return [float(v) for v in vector] + padding
    return [float(v) for v in vector]
