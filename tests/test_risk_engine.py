from api.schemas.response_schema import (
    FinancialImpactBand,
    RepeatOffenderPattern,
    RiskInput,
    SensitiveDataExposure,
)
from risk_engine.risk_calculator import calculate_risk


def test_low_boundary_score_0():
    risk = calculate_risk(
        RiskInput(
            financial_impact_band=FinancialImpactBand.LT_10K,
            sensitive_data_exposure=SensitiveDataExposure.NONE,
            repeat_offender_pattern=RepeatOffenderPattern.FIRST_TIME,
        )
    )
    assert risk.total_score == 0
    assert risk.risk_rating == "Low"


def test_medium_boundary_score_3():
    risk = calculate_risk(
        RiskInput(
            financial_impact_band=FinancialImpactBand.FROM_10K_TO_100K,
            sensitive_data_exposure=SensitiveDataExposure.CONFIDENTIAL,
            repeat_offender_pattern=RepeatOffenderPattern.FIRST_TIME,
        )
    )
    assert risk.total_score == 3
    assert risk.risk_rating == "Medium"


def test_high_example_score_5():
    risk = calculate_risk(
        RiskInput(
            financial_impact_band=FinancialImpactBand.FROM_100K_TO_1M,
            sensitive_data_exposure=SensitiveDataExposure.CONFIDENTIAL,
            repeat_offender_pattern=RepeatOffenderPattern.SECOND_INCIDENT_12M,
        )
    )
    assert risk.total_score == 5
    assert risk.risk_rating == "High"


def test_critical_boundary_score_8():
    risk = calculate_risk(
        RiskInput(
            financial_impact_band=FinancialImpactBand.GT_1M,
            sensitive_data_exposure=SensitiveDataExposure.REGULATED_HIGHLY_SENSITIVE,
            repeat_offender_pattern=RepeatOffenderPattern.THREE_PLUS_12M,
        )
    )
    assert risk.total_score == 8
    assert risk.risk_rating == "Critical"
