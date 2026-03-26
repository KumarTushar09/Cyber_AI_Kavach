HIGH_RISK_KEYWORDS = ["mod", "crack", "hack", "premium", "patched"]


def static_apk_scan(apk_name: str) -> dict:
    lowered = apk_name.lower()
    flags = []
    if not lowered.endswith(".apk"):
        flags.append("invalid_extension")
    if any(term in lowered for term in HIGH_RISK_KEYWORDS):
        flags.append("suspicious_filename_pattern")
    if " " in apk_name:
        flags.append("filename_whitespace_signal")

    severity = "low"
    if len(flags) >= 2:
        severity = "high"

    return {"apk_name": apk_name, "flags": flags, "severity": severity}
