# URL-only mode: keep non-URL analysis imports commented for later phases.
# from agents.apk_analysis_agent import analyze_apk
# from agents.sms_analysis_agent import analyze_sms
from api.schemas.response_schema import RiskInput
from services.analysis_service import run_url_two_pass


def _recommendation_for_rating(rating: str) -> str:
    rating_upper = rating.lower()
    if rating_upper in {"high", "critical"}:
        return "Block and escalate"
    if rating_upper == "medium":
        return "Allow with enhanced verification"
    return "Allow with monitoring"


async def orchestrate_analysis(content_type: str, content: str, risk_input: RiskInput | None = None) -> dict:
    if content_type != "url":
        return {
            "analysis": {"signals": {}, "pattern": {"pattern": "unsupported_content_type", "suspicion_score": 0}},
            "risk": {"risk_rating": "Unknown", "total_score": 0},
            "recommendation": "Unsupported content type",
        }

    # URL-only, LLM-only two-pass flow
    url_result = await run_url_two_pass(content, risk_input=risk_input)
    score = (url_result.get("risk") or {}).get("total_score", 0)
    pattern = {"pattern": "url_llm_only", "suspicion_score": score}

    if url_result.get("needs_risk_input"):
        recommendation = "Collect risk inputs for evaluation"
    elif url_result.get("risk"):
        recommendation = _recommendation_for_rating(url_result["risk"].get("risk_rating", "Low"))
    else:
        recommendation = url_result.get("recommendation", "ALLOW")

    return {
        "analysis": {
            "signals": {
                "llm_pass1": url_result["llm_pass1"],
                "llm_pass2": url_result["llm_pass2"],
            },
            "pattern": pattern,
        },
        "risk": url_result["risk"],
        "url": url_result["url"],
        "needs_risk_input": url_result.get("needs_risk_input", False),
        "required_questions": url_result.get("required_questions", []),
        "pass1_recommendation": url_result.get("recommendation", "ALLOW"),
        "recommendation": recommendation,
    }
