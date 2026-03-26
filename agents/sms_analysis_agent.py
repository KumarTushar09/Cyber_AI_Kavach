from tools.sms_tool import inspect_sms


def analyze_sms(sms_text: str) -> dict:
    return inspect_sms(sms_text)
