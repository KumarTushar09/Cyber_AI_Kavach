from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile

from agents.orchestrator_agent import orchestrate_analysis
from api.schemas.response_schema import (
    APIResponse,
    FinancialImpactBand,
    RepeatOffenderPattern,
    RiskInput,
    SensitiveDataExposure,
)
from backend.auth import require_scopes
from services.storage_service import upload_to_s3

router = APIRouter(tags=["upload"], dependencies=[Depends(require_scopes("upload:write"))])


def _target_dir(analysis_type: str) -> Path:
    if analysis_type == "apk":
        return Path("uploads/temp_apk")
    if analysis_type == "sms":
        return Path("uploads/temp_sms")
    return Path("uploads/temp_urls")


@router.post("/upload/file", response_model=APIResponse)
async def upload_file_for_analysis(
    analysis_type: str = Form(...),
    financial_impact_band: FinancialImpactBand = Form(...),
    sensitive_data_exposure: SensitiveDataExposure = Form(...),
    repeat_offender_pattern: RepeatOffenderPattern = Form(...),
    file: UploadFile = File(...),
) -> APIResponse:
    trace_id = str(uuid4())

    safe_type = analysis_type.strip().lower()
    if safe_type not in {"url", "sms", "apk"}:
        return APIResponse(
            status="error",
            trace_id=trace_id,
            data={"reason": "analysis_type must be one of: url, sms, apk"},
        )

    target_dir = _target_dir(safe_type)
    target_dir.mkdir(parents=True, exist_ok=True)

    file_id = f"{uuid4()}_{file.filename}"
    file_path = target_dir / file_id
    raw = await file.read()
    file_path.write_bytes(raw)

    s3_result = upload_to_s3(str(file_path), object_key=f"{safe_type}/{file_id}")

    if safe_type == "apk":
        content_for_analysis = file.filename
    else:
        content_for_analysis = raw.decode("utf-8", errors="ignore").strip() or file.filename

    risk_input = RiskInput(
        financial_impact_band=financial_impact_band,
        sensitive_data_exposure=sensitive_data_exposure,
        repeat_offender_pattern=repeat_offender_pattern,
    )
    analysis_result = await orchestrate_analysis(
        content_type=safe_type,
        content=content_for_analysis,
        risk_input=risk_input,
    )

    return APIResponse(
        trace_id=trace_id,
        data={
            "analysis_type": safe_type,
            "file_name": file.filename,
            "local_path": str(file_path),
            "s3_upload": s3_result,
            "result": analysis_result,
        },
    )
