from uuid import uuid4

from fastapi import APIRouter, Depends

from agents.orchestrator_agent import orchestrate_analysis
from api.schemas.response_schema import APIResponse, AnalyzeSMSRequest
from backend.auth import require_scopes

router = APIRouter(tags=["analysis"], dependencies=[Depends(require_scopes("analysis:read"))])


@router.post("/analyze/sms", response_model=APIResponse)
async def analyze_sms_endpoint(request: AnalyzeSMSRequest) -> APIResponse:
    trace_id = str(uuid4())
    result = await orchestrate_analysis(content_type="sms", content=request.sms_text, risk_input=request.risk_input)
    return APIResponse(trace_id=trace_id, data=result)
