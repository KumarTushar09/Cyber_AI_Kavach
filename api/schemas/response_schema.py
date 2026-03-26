from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FinancialImpactBand(str, Enum):
    LT_10K = "LT_10K"
    FROM_10K_TO_100K = "FROM_10K_TO_100K"
    FROM_100K_TO_1M = "FROM_100K_TO_1M"
    GT_1M = "GT_1M"


class SensitiveDataExposure(str, Enum):
    NONE = "NONE"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    CONFIDENTIAL = "CONFIDENTIAL"
    REGULATED_HIGHLY_SENSITIVE = "REGULATED_HIGHLY_SENSITIVE"


class RepeatOffenderPattern(str, Enum):
    FIRST_TIME = "FIRST_TIME"
    SECOND_INCIDENT_12M = "SECOND_INCIDENT_12M"
    THREE_PLUS_12M = "THREE_PLUS_12M"


class RiskInput(BaseModel):
    financial_impact_band: FinancialImpactBand
    sensitive_data_exposure: SensitiveDataExposure
    repeat_offender_pattern: RepeatOffenderPattern


class AnalyzeURLRequest(BaseModel):
    url: str = Field(min_length=4)
    risk_input: RiskInput | None = None


class AnalyzeSMSRequest(BaseModel):
    sms_text: str = Field(min_length=1)
    risk_input: RiskInput


class AnalyzeAPKRequest(BaseModel):
    apk_name: str = Field(min_length=1)
    risk_input: RiskInput


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=2)


class FraudReportRequest(BaseModel):
    incident_id: str = Field(min_length=1)
    notes: str = Field(default="")


class RiskBreakdown(BaseModel):
    financial_impact_points: int
    sensitive_data_points: int
    repeat_offender_points: int
    total_score: int
    risk_rating: str
    rationale: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel):
    status: str = "success"
    trace_id: str
    data: dict[str, Any]
    errors: list[ErrorDetail] | None = None
