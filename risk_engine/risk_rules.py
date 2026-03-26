from api.schemas.response_schema import (
    FinancialImpactBand,
    RepeatOffenderPattern,
    SensitiveDataExposure,
)


FINANCIAL_IMPACT_POINTS = {
    FinancialImpactBand.LT_10K: 0,
    FinancialImpactBand.FROM_10K_TO_100K: 1,
    FinancialImpactBand.FROM_100K_TO_1M: 2,
    FinancialImpactBand.GT_1M: 3,
}

SENSITIVE_DATA_POINTS = {
    SensitiveDataExposure.NONE: 0,
    SensitiveDataExposure.INTERNAL_ONLY: 1,
    SensitiveDataExposure.CONFIDENTIAL: 2,
    SensitiveDataExposure.REGULATED_HIGHLY_SENSITIVE: 3,
}

REPEAT_OFFENDER_POINTS = {
    RepeatOffenderPattern.FIRST_TIME: 0,
    RepeatOffenderPattern.SECOND_INCIDENT_12M: 1,
    RepeatOffenderPattern.THREE_PLUS_12M: 2,
}


def rating_from_total(total_score: int) -> str:
    if 0 <= total_score <= 2:
        return "Low"
    if 3 <= total_score <= 4:
        return "Medium"
    if 5 <= total_score <= 6:
        return "High"
    return "Critical"
