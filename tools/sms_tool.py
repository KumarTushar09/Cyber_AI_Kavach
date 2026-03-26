SUSPICIOUS_WORDS = ["otp", "urgent", "claim", "winner", "verify", "click", "update", "suspended"]


def inspect_sms(text: str) -> dict:
    lowered = text.lower()
    flags = []
    if any(word in lowered for word in SUSPICIOUS_WORDS):
        flags.append("suspicious_vocabulary")
    if "http://" in lowered or "https://" in lowered:
        flags.append("embedded_link")
    if any(ch.isdigit() for ch in lowered) and "otp" in lowered:
        flags.append("otp_request_pattern")
    if "immediately" in lowered or "now" in lowered:
        flags.append("urgency_language")

    severity = "low"
    if len(flags) >= 3:
        severity = "high"
    elif len(flags) == 2:
        severity = "medium"

    return {"text": text, "flags": flags, "severity": severity}
