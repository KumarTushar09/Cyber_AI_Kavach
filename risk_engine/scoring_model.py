from api.schemas.response_schema import RiskBreakdown, RiskInput
from risk_engine.risk_rules import (
    FINANCIAL_IMPACT_POINTS,
    REPEAT_OFFENDER_POINTS,
    SENSITIVE_DATA_POINTS,
    rating_from_total,
)


def score_risk(risk_input: RiskInput) -> RiskBreakdown:
    financial_points = FINANCIAL_IMPACT_POINTS[risk_input.financial_impact_band]
    sensitive_points = SENSITIVE_DATA_POINTS[risk_input.sensitive_data_exposure]
    repeat_points = REPEAT_OFFENDER_POINTS[risk_input.repeat_offender_pattern]

    total_score = financial_points + sensitive_points + repeat_points
    risk_rating = rating_from_total(total_score)

    rationale = (
        f"Financial impact={financial_points}, sensitive data={sensitive_points}, "
        f"repeat offender={repeat_points}; total={total_score} => {risk_rating}."
    )

    return RiskBreakdown(
        financial_impact_points=financial_points,
        sensitive_data_points=sensitive_points,
        repeat_offender_points=repeat_points,
        total_score=total_score,
        risk_rating=risk_rating,
        rationale=rationale,
    )
