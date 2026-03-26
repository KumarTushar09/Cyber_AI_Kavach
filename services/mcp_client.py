from typing import Any

import httpx

from backend.config import settings
from services.retry import retry_async


def _target_url() -> str:
    base = settings.MCP_SERVER_URL.strip()
    if not base:
        return ""

    path = settings.MCP_GATEWAY_PATH.strip()
    if not path:
        return base.rstrip("/")
    return f"{base.rstrip('/')}/{path.lstrip('/').rstrip('/')}"


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = settings.MCP_AUTH_TOKEN.strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _tool_timeout_seconds(tool_name: str) -> float:
    timeout_by_tool = {
        "chat": settings.MCP_TIMEOUT_CHAT_SECONDS,
        "embed": settings.MCP_TIMEOUT_EMBED_SECONDS,
        "pg_query": settings.MCP_TIMEOUT_PG_QUERY_SECONDS,
        "qdrant_search": settings.MCP_TIMEOUT_QDRANT_SECONDS,
        "s3_get_put": settings.MCP_TIMEOUT_S3_SECONDS,
        "health": settings.MCP_TIMEOUT_HEALTH_SECONDS,
    }
    selected = timeout_by_tool.get(tool_name, settings.MCP_GATEWAY_TIMEOUT_SECONDS)
    # Respect gateway hard cap.
    return max(1.0, min(float(selected), 600.0))


async def call_tool(tool_name: str, tool_input: dict[str, Any] | None = None) -> dict[str, Any]:
    target_base_url = _target_url()
    if not target_base_url:
        return {"status": "skipped", "reason": "MCP endpoint is not configured."}

    target_url = f"{target_base_url}/tools/{tool_name}"
    payload = tool_input or {}
    timeout_seconds = _tool_timeout_seconds(tool_name)
    max_attempts = max(1, min(settings.RETRY_MAX_ATTEMPTS, 5))

    async def _send_once() -> dict[str, Any]:
        connect_timeout = min(10.0, timeout_seconds)
        timeout = httpx.Timeout(timeout=timeout_seconds, connect=connect_timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(target_url, json=payload, headers=_headers())
            response.raise_for_status()
            data = response.json() if response.content else {}
            return {
                "status": "ok",
                "tool": tool_name,
                "target_url": target_url,
                "data": data if isinstance(data, dict) else {"result": data},
            }

    try:
        return await retry_async(
            _send_once,
            attempts=max_attempts,
            base_delay_seconds=settings.RETRY_BASE_DELAY_SECONDS,
            retry_on=(httpx.RequestError, httpx.HTTPStatusError),
        )
    except httpx.HTTPStatusError as exc:
        return {
            "status": "error",
            "tool": tool_name,
            "target_url": target_url,
            "reason": f"MCP gateway returned HTTP {exc.response.status_code}.",
        }
    except httpx.RequestError as exc:
        return {
            "status": "error",
            "tool": tool_name,
            "target_url": target_url,
            "reason": f"Failed to reach MCP gateway: {str(exc)}",
        }


async def health_check() -> dict[str, Any]:
    return await call_tool("health", {})
