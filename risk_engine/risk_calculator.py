from api.schemas.response_schema import RiskBreakdown, RiskInput
from risk_engine.scoring_model import score_risk


def calculate_risk(risk_input: RiskInput) -> RiskBreakdown:
    return score_risk(risk_input)
