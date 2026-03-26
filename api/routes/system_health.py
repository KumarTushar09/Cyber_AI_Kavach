from uuid import uuid4

from fastapi import APIRouter, Depends

from api.schemas.response_schema import APIResponse
from backend.auth import require_scopes
from backend.config import settings
from database.postgres_client import get_postgres_client
from database.qdrant_client import get_qdrant_client
from services.llm_service import call_llm_router
from services.mcp_client import health_check as mcp_health_check
from services.storage_service import get_s3_health

router = APIRouter(tags=["system"], dependencies=[Depends(require_scopes("system:read"))])


@router.get("/system/readiness", response_model=APIResponse)
async def readiness() -> APIResponse:
    trace_id = str(uuid4())

    if settings.USE_MCP:
        mcp = await mcp_health_check()
        mcp_data = mcp.get("data", {}) if isinstance(mcp, dict) else {}
        checks = mcp_data.get("checks", {}) if isinstance(mcp_data, dict) else {}

        router_status = checks.get("ollama_router") or checks.get("router") or "fail"
        postgres_status = checks.get("postgres", "fail")
        qdrant_status = checks.get("qdrant", "ok")
        s3_status = checks.get("s3", "fail")

        component_statuses = [
            router_status,
            postgres_status,
            qdrant_status,
            s3_status,
        ]
        gateway_status = mcp_data.get("status", "degraded")
        ok_values = {"ok", "disabled"}
        overall = (
            "ready"
            if mcp.get("status") == "ok"
            and gateway_status == "ok"
            and all(item in ok_values for item in component_statuses)
            else "degraded"
        )

        return APIResponse(
            trace_id=trace_id,
            data={
                "overall": overall,
                "mcp_gateway": mcp,
                "checks": checks,
            },
        )

    postgres = get_postgres_client()
    qdrant = get_qdrant_client()
    llm = await call_llm_router({"prompt_type": "health_check", "content": "ping"})
    s3 = get_s3_health()

    components = {
        "postgres": postgres,
        "qdrant": qdrant,
        "llm_router": llm,
        "s3": s3,
    }
    statuses = [component.get("status") for component in components.values()]
    overall = "degraded" if "error" in statuses else "ready"

    return APIResponse(
        trace_id=trace_id,
        data={
            "overall": overall,
            **components,
        },
    )
