from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.middleware import reset_rate_limit_state

client = TestClient(app)
AUTH_HEADERS = {settings.AUTH_HEADER_NAME: settings.API_KEY}


RISK_INPUT = {
    "financial_impact_band": "FROM_100K_TO_1M",
    "sensitive_data_exposure": "CONFIDENTIAL",
    "repeat_offender_pattern": "SECOND_INCIDENT_12M",
}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "X-Request-ID" in response.headers


def test_url_analysis_endpoint():
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "https://secure-bank-login.com/verify", "risk_input": RISK_INPUT},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "recommendation" in body["data"]


def test_sms_analysis_endpoint():
    response = client.post(
        "/api/v1/analyze/sms",
        json={"sms_text": "Urgent! Verify OTP now at https://x.co", "risk_input": RISK_INPUT},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "analysis" in body["data"]


def test_apk_analysis_endpoint():
    response = client.post(
        "/api/v1/analyze/apk",
        json={"apk_name": "premium_crack_app.apk", "risk_input": RISK_INPUT},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["risk"]["risk_rating"] in {"Low", "Medium", "High", "Critical"}


def test_knowledge_query_endpoint():
    response = client.post("/api/v1/knowledge/query", json={"question": "What is phishing?"}, headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "answer" in body["data"]


def test_readiness_endpoint():
    response = client.get("/api/v1/system/readiness", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "overall" in body["data"]


def test_upload_endpoint_sms():
    files = {"file": ("sample_sms.txt", b"Urgent update your account now", "text/plain")}
    data = {
        "analysis_type": "sms",
        "financial_impact_band": "FROM_10K_TO_100K",
        "sensitive_data_exposure": "INTERNAL_ONLY",
        "repeat_offender_pattern": "FIRST_TIME",
    }
    response = client.post("/api/v1/upload/file", data=data, files=files, headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"success", "error"}
    assert "s3_upload" in body["data"]


def test_validation_error_envelope():
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "bad", "risk_input": RISK_INPUT},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["errors"][0]["code"] == "VALIDATION_ERROR"


def test_api_key_required_for_protected_endpoint():
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "https://secure-bank-login.com/verify", "risk_input": RISK_INPUT},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["errors"][0]["code"] == "AUTH_REQUIRED"


def test_scope_required_for_endpoint():
    original_scopes = settings.API_KEY_SCOPES
    settings.API_KEY_SCOPES = "knowledge:read"
    try:
        response = client.post(
            "/api/v1/analyze/url",
            json={"url": "https://secure-bank-login.com/verify", "risk_input": RISK_INPUT},
            headers=AUTH_HEADERS,
        )
    finally:
        settings.API_KEY_SCOPES = original_scopes

    assert response.status_code == 403
    body = response.json()
    assert body["errors"][0]["code"] == "AUTH_FORBIDDEN"


def test_rate_limit_blocks_excess_requests():
    original_enabled = settings.RATE_LIMIT_ENABLED
    original_requests = settings.RATE_LIMIT_REQUESTS
    original_window = settings.RATE_LIMIT_WINDOW_SECONDS
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_REQUESTS = 1
    settings.RATE_LIMIT_WINDOW_SECONDS = 60
    reset_rate_limit_state()

    try:
        first_response = client.get("/api/v1/system/readiness", headers=AUTH_HEADERS)
        second_response = client.get("/api/v1/system/readiness", headers=AUTH_HEADERS)
    finally:
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_REQUESTS = original_requests
        settings.RATE_LIMIT_WINDOW_SECONDS = original_window
        reset_rate_limit_state()

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json()["errors"][0]["code"] == "RATE_LIMIT_EXCEEDED"
    assert second_response.headers["Retry-After"]


def test_readiness_includes_s3_status():
    response = client.get("/api/v1/system/readiness", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "s3" in body["data"]
