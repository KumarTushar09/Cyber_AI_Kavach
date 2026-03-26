def detect_pattern(indicators: dict) -> dict:
    tool_flags = indicators.get("tool", {}).get("flags", [])
    llm_status = indicators.get("llm", {}).get("status", "skipped")
    suspicion_score = len(tool_flags)

    if llm_status == "ok":
        suspicion_score += 1

    pattern = "benign"
    if suspicion_score >= 4:
        pattern = "coordinated_fraud_pattern"
    elif suspicion_score >= 2:
        pattern = "suspicious_pattern"

    return {
        "pattern": pattern,
        "suspicion_score": suspicion_score,
        "indicators": indicators,
    }
