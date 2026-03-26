def build_plan(content_type: str) -> dict:
    return {"content_type": content_type, "steps": ["tool_analysis", "llm_analysis", "risk_scoring"]}
