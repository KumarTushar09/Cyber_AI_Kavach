from typing import Any

import httpx

from backend.config import settings
from services.mcp_client import call_tool
from services.retry import retry_async


async def generate_completion(prompt: str, *, prompt_type: str, model: str | None = None) -> dict[str, Any]:
    target_model = model or settings.LLM_MODEL
    if settings.USE_MCP:
        mcp_result = await call_tool(
            "chat",
            {
                "prompt": f"[{prompt_type}]\n{prompt}",
                "model": target_model,
                "context": {"prompt_type": prompt_type},
            },
        )
        if mcp_result.get("status") != "ok":
            return mcp_result

        data = mcp_result.get("data") or {}
        text = data.get("text") or data.get("response") or ""
        return {
            "status": "ok",
            "target_url": mcp_result.get("target_url", settings.MCP_SERVER_URL),
            "data": {
                "response": text,
                "model": data.get("model", target_model),
                "done": bool(data.get("done", True)),
                "usage": data.get("usage", {}),
                "latency_ms": data.get("latency_ms"),
                "tool": "chat",
            },
        }

    base_url = settings.LLM_ROUTER_URL.strip()
    analyze_path = settings.LLM_ANALYZE_PATH.strip()
    # Honor configured timeout with an upper guardrail; allow longer generation windows when required.
    timeout_seconds = max(5.0, min(settings.LLM_TIMEOUT_SECONDS, 600.0))
    max_attempts = max(1, min(settings.RETRY_MAX_ATTEMPTS, 5))

    if not base_url:
        return {"status": "skipped", "reason": "LLM endpoint is not configured."}

    target_url = f"{base_url.rstrip('/')}/{analyze_path.lstrip('/')}"
    payload = {
        "model": target_model,
        "prompt": f"[{prompt_type}]\n{prompt}",
        "stream": False,
    }

    async def _send_once() -> dict[str, Any]:
        # Clamp connect timeout so unreachable endpoints fail fast instead of hanging the request thread.
        connect_timeout = min(10.0, timeout_seconds)
        timeout = httpx.Timeout(timeout=timeout_seconds, connect=connect_timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(target_url, json=payload)
            response.raise_for_status()
            return {"status": "ok", "target_url": target_url, "data": response.json()}

    try:
        result = await retry_async(
            _send_once,
            attempts=max_attempts,
            base_delay_seconds=settings.RETRY_BASE_DELAY_SECONDS,
            retry_on=(httpx.RequestError, httpx.HTTPStatusError),
        )
        return result
    except httpx.HTTPStatusError as exc:
        return {
            "status": "error",
            "target_url": target_url,
            "reason": f"LLM endpoint returned HTTP {exc.response.status_code}.",
        }
    except httpx.RequestError as exc:
        return {
            "status": "error",
            "target_url": target_url,
            "reason": f"Failed to reach LLM endpoint: {str(exc)}",
        }


async def call_llm_router(payload: dict[str, Any]) -> dict[str, Any]:
    prompt_type = str(payload.get("prompt_type", "generic"))
    content = str(payload.get("content", ""))
    model = payload.get("model")
    return await generate_completion(content, prompt_type=prompt_type, model=model)
