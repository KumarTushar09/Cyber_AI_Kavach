import json
import re
from pathlib import Path
from typing import Any

from api.schemas.response_schema import RiskInput
from risk_engine.risk_calculator import calculate_risk
from services.llm_service import generate_completion


DEFAULT_PASS1_PROMPT = """You are a cybersecurity expert specializing in URL phishing detection.

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations outside the JSON.

URL to Analyze:
{url}

Analyze the URL and return ONLY the JSON response:
"""

DEFAULT_PASS2_PROMPT = """You are a cybersecurity assistant.

Given a JSON response from a threat analysis system, summarize it in 4-5 concise lines.

Focus on:
- Overall risk level and recommendation (ALLOW / BLOCK / REVIEW)
- Whether it is phishing or malicious
- Key indicators (1-2 most important findings)
- Confidence level
- Simple user advice

Keep the summary clear, non-technical, and easy for end users to understand.
Avoid repeating raw JSON fields or technical jargon.

Threat analysis JSON:
{pass1_json}

Risk evaluation (may be empty when not required):
- Financial impact points: {financial_impact_points}
- Sensitive data points: {sensitive_data_points}
- Repeat offender points: {repeat_offender_points}
- Total score: {total_score}
- Risk rating: {risk_rating}
- Risk rationale: {risk_rationale}
"""


def _load_prompt(path: Path, default_text: str) -> str:
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        return text or default_text
    return default_text


def _safe_format(template: str, values: dict[str, Any]) -> str:
    # Replace only simple named placeholders and leave all other braces untouched.
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return re.sub(r"{([a-zA-Z_][a-zA-Z0-9_]*)}", _replace, template)


def _extract_json(raw_text: str) -> tuple[dict[str, Any], str]:
    stripped = raw_text.strip()
    if not stripped:
        return {}, "empty_response"

    try:
        return json.loads(stripped), "parsed_full"
    except Exception:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            return json.loads(candidate), "parsed_substring"
        except Exception:
            return {}, "invalid_json"

    return {}, "invalid_json"


def _normalize_recommendation(value: Any) -> str:
    recommendation = str(value or "").strip().upper()
    if recommendation in {"BLOCK", "WARN", "ALLOW"}:
        return recommendation
    return "ALLOW"


def _requires_risk_evaluation(recommendation: str) -> bool:
    return recommendation in {"BLOCK", "WARN"}


async def run_url_two_pass(url: str, risk_input: RiskInput | None = None) -> dict[str, Any]:
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"

    # Pass 1 MUST come from prompts/url_analysis_prompt.txt
    pass1_template = _load_prompt(prompts_dir / "url_analysis_prompt.txt", DEFAULT_PASS1_PROMPT)
    pass1_prompt = _safe_format(pass1_template, {"url": url})
    llm_pass1 = await generate_completion(pass1_prompt, prompt_type="url_analysis_json")
    llm_pass1_status = llm_pass1.get("status", "unknown")
    llm_pass1_reason = llm_pass1.get("reason", "")
    llm_pass1_text = (
        llm_pass1.get("data", {}).get("response", "")
        or llm_pass1.get("data", {}).get("message", "")
        or llm_pass1_reason
    )
    pass1_json, pass1_parse_reason = _extract_json(llm_pass1_text)
    llm_pass1_payload = {
        "prompt_type": "url_analysis_json",
        "prompt": pass1_prompt,
        "raw_response": llm_pass1_text,
        "parsed_json": pass1_json,
        "status": llm_pass1_status,
        "parse_reason": pass1_parse_reason,
    }

    if llm_pass1_status != "ok":
        fallback_message = llm_pass1_reason or "LLM endpoint unavailable"
        return {
            "url": url,
            "needs_risk_input": False,
            "required_questions": [],
            "recommendation": "ALLOW",
            "llm_pass1": llm_pass1_payload,
            "llm_pass2": {
                "prompt_type": "url_summary",
                "prompt": "",
                "raw_response": fallback_message,
                "status": llm_pass1_status,
            },
            "risk": None,
        }

    recommendation = _normalize_recommendation(pass1_json.get("recommendation"))
    needs_risk_input = _requires_risk_evaluation(recommendation) and risk_input is None

    required_questions = [
        {
            "field": "financial_impact_band",
            "label": "Financial impact",
            "options": ["LT_10K", "FROM_10K_TO_100K", "FROM_100K_TO_1M", "GT_1M"],
        },
        {
            "field": "sensitive_data_exposure",
            "label": "Sensitive data exposure",
            "options": ["NONE", "INTERNAL_ONLY", "CONFIDENTIAL", "REGULATED_HIGHLY_SENSITIVE"],
        },
        {
            "field": "repeat_offender_pattern",
            "label": "Repeat offender pattern",
            "options": ["FIRST_TIME", "SECOND_INCIDENT_12M", "THREE_PLUS_12M"],
        },
    ]

    risk = None
    if risk_input is not None:
        risk = calculate_risk(risk_input).model_dump()

    pass2_template = _load_prompt(prompts_dir / "url_risk_prompt.txt", DEFAULT_PASS2_PROMPT)
    pass2_prompt_values = {
        "url": url,
        "pass1_json": json.dumps(pass1_json, indent=2, ensure_ascii=True),
        "financial_impact_points": (risk or {}).get("financial_impact_points", ""),
        "sensitive_data_points": (risk or {}).get("sensitive_data_points", ""),
        "repeat_offender_points": (risk or {}).get("repeat_offender_points", ""),
        "total_score": (risk or {}).get("total_score", ""),
        "risk_rating": (risk or {}).get("risk_rating", ""),
        "risk_rationale": (risk or {}).get("rationale", ""),
    }
    pass2_prompt = _safe_format(pass2_template, pass2_prompt_values)

    llm_pass2_text = ""
    llm_pass2_status = "skipped"
    if not needs_risk_input:
        llm_pass2 = await generate_completion(pass2_prompt, prompt_type="url_summary")
        llm_pass2_status = llm_pass2.get("status", "unknown")
        llm_pass2_text = llm_pass2.get("data", {}).get("response", "") or llm_pass2.get("data", {}).get("message", "") or ""

    return {
        "url": url,
        "needs_risk_input": needs_risk_input,
        "required_questions": required_questions if needs_risk_input else [],
        "recommendation": recommendation,
        "llm_pass1": llm_pass1_payload,
        "llm_pass2": {
            "prompt_type": "url_summary",
            "prompt": pass2_prompt,
            "raw_response": llm_pass2_text,
            "status": llm_pass2_status,
        },
        "risk": risk,
    }
