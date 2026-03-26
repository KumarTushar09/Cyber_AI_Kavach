from uuid import uuid4

from fastapi import APIRouter, Depends

from api.schemas.response_schema import APIResponse, KnowledgeQueryRequest
from backend.auth import require_scopes
from services.rag_service import query_rag

router = APIRouter(tags=["knowledge"], dependencies=[Depends(require_scopes("knowledge:read"))])


@router.post("/knowledge/query", response_model=APIResponse)
async def query_knowledge(request: KnowledgeQueryRequest) -> APIResponse:
    trace_id = str(uuid4())
    rag_result = await query_rag(request.question)
    return APIResponse(trace_id=trace_id, data=rag_result)
