from tools.apk_tool import static_apk_scan


def analyze_apk(apk_name: str) -> dict:
    return static_apk_scan(apk_name)
