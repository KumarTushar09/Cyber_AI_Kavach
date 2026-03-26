from uuid import uuid4

from fastapi import APIRouter, Depends

from api.schemas.response_schema import APIResponse, FraudReportRequest
from backend.auth import require_scopes

router = APIRouter(tags=["fraud"], dependencies=[Depends(require_scopes("fraud:write"))])


@router.post("/report/fraud", response_model=APIResponse)
def report_fraud(request: FraudReportRequest) -> APIResponse:
    trace_id = str(uuid4())
    return APIResponse(trace_id=trace_id, data={"incident_id": request.incident_id, "saved": True, "notes": request.notes})
