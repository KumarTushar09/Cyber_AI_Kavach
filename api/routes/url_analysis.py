from uuid import uuid4

from fastapi import APIRouter, Query

from agents.orchestrator_agent import orchestrate_analysis
from api.schemas.response_schema import APIResponse, AnalyzeURLRequest
# URL-only local mode: auth dependency is intentionally bypassed.
# from backend.auth import require_scopes

router = APIRouter(tags=["analysis"])


@router.post("/analyze/url", response_model=APIResponse)
async def analyze_url_endpoint(
    request: AnalyzeURLRequest,
    compact: bool = Query(default=True, description="Return minimal URL-only response shape when true."),
) -> APIResponse:
    trace_id = str(uuid4())
    result = await orchestrate_analysis(content_type="url", content=request.url, risk_input=request.risk_input)

    if compact:
        llm_pass1 = result.get("analysis", {}).get("signals", {}).get("llm_pass1", {})
        llm_pass2 = result.get("analysis", {}).get("signals", {}).get("llm_pass2", {})
        risk = result.get("risk", {})
        compact_result = {
            "url": result.get("url", request.url),
            "needs_risk_input": result.get("needs_risk_input", False),
            "required_questions": result.get("required_questions", []),
            "pass1": {
                "recommendation": result.get("pass1_recommendation", "ALLOW"),
                "parsed_json": llm_pass1.get("parsed_json", {}),
            },
            "llm_summary": {
                "status": llm_pass2.get("status", "unknown"),
                "prompt_type": llm_pass2.get("prompt_type", "url_summary"),
                "response": llm_pass2.get("raw_response", ""),
            },
            "risk": (
                {
                    "rating": risk.get("risk_rating", "Unknown"),
                    "score": risk.get("total_score", 0),
                }
                if isinstance(risk, dict) and risk
                else None
            ),
            "recommendation": result.get("recommendation", "Allow with monitoring"),
        }
        return APIResponse(trace_id=trace_id, data=compact_result)

    return APIResponse(trace_id=trace_id, data=result)
