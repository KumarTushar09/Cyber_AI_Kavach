#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

printf "Running smoke tests against %s\n" "$BASE_URL"

curl -fsS "$BASE_URL/health" >/dev/null

echo "Health check passed"

curl -fsS -X POST "$BASE_URL/api/v1/analyze/url" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://secure-bank-login.com/verify","risk_input":{"financial_impact_band":"FROM_100K_TO_1M","sensitive_data_exposure":"CONFIDENTIAL","repeat_offender_pattern":"SECOND_INCIDENT_12M"}}' >/dev/null

echo "URL analysis endpoint passed"

curl -fsS -X POST "$BASE_URL/api/v1/knowledge/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is phishing?"}' >/dev/null

echo "Knowledge query endpoint passed"

curl -fsS "$BASE_URL/api/v1/system/readiness" >/dev/null

echo "Readiness endpoint passed"

echo "Smoke tests completed successfully"
