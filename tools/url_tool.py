from urllib.parse import urlparse

SUSPICIOUS_TERMS = ["verify", "bank", "login", "urgent", "secure", "wallet", "kyc"]

def inspect_url(url: str) -> dict:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    flags = []
    if not host:
        flags.append("missing_host")
    if parsed.scheme != "https":
        flags.append("non_https")
    if host.count("-") >= 2:
        flags.append("hyphenated_domain")
    if any(term in path for term in SUSPICIOUS_TERMS):
        flags.append("suspicious_path_terms")
    if any(char.isdigit() for char in host):
        flags.append("numeric_domain_signal")

    severity = "low"
    if len(flags) >= 3:
        severity = "high"
    elif len(flags) == 2:
        severity = "medium"

    return {"url": url, "flags": flags, "severity": severity}
