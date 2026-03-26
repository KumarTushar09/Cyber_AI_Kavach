def decide_response(analysis: dict, risk: dict) -> dict:
    rating = risk.get("risk_rating", "Low")
    recommendation = "Allow with monitoring"
    if rating in {"High", "Critical"}:
        recommendation = "Block and escalate for manual review"
    elif rating == "Medium":
        recommendation = "Allow with enhanced verification"

    return {
        "analysis": analysis,
        "risk": risk,
        "recommendation": recommendation,
    }
