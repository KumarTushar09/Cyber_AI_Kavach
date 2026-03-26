# Cyber AI Kavach - Instance 1

## Services
- Frontend: Next.js UI
- Backend: FastAPI API gateway
- Risk Engine: Simple unweighted scoring model
- Analysis Pipeline: tool heuristics + optional LLM router integration
- Data Integrations: Postgres/Qdrant/S3 placeholders with graceful fallback

## Risk Scoring (v1)
- Financial impact: <10K=0, 10K-100K=1, 100K-1M=2, >1M=3
- Sensitive data: none=0, internal-only=1, confidential=2, regulated/highly sensitive=3
- Repeat offender: first-time=0, second incident in 12m=1, three+ in 12m=2
- Total = sum (max 8)
- Rating: 0-2 Low, 3-4 Medium, 5-6 High, 7-8 Critical

## Run
```bash
docker compose up --build
```

## Key API Endpoints
- POST /api/v1/analyze/url
- POST /api/v1/analyze/sms
- POST /api/v1/analyze/apk
- POST /api/v1/knowledge/query
- POST /api/v1/report/fraud
- POST /api/v1/upload/file
- GET /api/v1/system/readiness

## Integration Notes
- If `LLM_ROUTER_URL` is empty, analysis continues with tool signals only.
- If Postgres/Qdrant envs are empty, threat-intelligence lookups are skipped safely.
- If `S3_BUCKET_NAME` is empty, upload service returns a skipped status.

## Hardening (Phase 4)
- Structured JSON request logs with request id.
- Standardized error envelope for HTTP, validation, and internal exceptions.
- Optional API key protection via `AUTH_HEADER_NAME` + `API_KEY` in `backend/.env`.
- Retry policy applied to external LLM calls (`RETRY_MAX_ATTEMPTS`, `RETRY_BASE_DELAY_SECONDS`).

## Required From Your End

### 1) Instance 2 (LLM Router)
- LLM router base URL
- Example: `http://10.x.x.x:8001`

### 2) Instance 3 (Postgres)
- POSTGRES_HOST
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD

### 3) Instance 3 (Qdrant)
- QDRANT_HOST
- QDRANT_PORT (default: 6333)
- QDRANT_COLLECTION_THREATS (default: threat_vectors)

### 4) S3 Upload
- AWS_REGION
- S3_BUCKET_NAME

### 5) Network/Access Checks
- Instance 1 can reach Instance 2 on LLM router port
- Instance 1 can reach Instance 3 Postgres port
- Instance 1 can reach Instance 3 Qdrant port
- IAM/credentials allow upload to the S3 bucket

### Where These Go
- Environment template: `backend/.env`

### Current Status
- These values are intentionally commented out in `backend/.env`.
- Until configured, APIs continue using graceful fallback behavior.

## Testing
- Unit/API tests: `pytest -q`
- Python syntax check: `python3 -m compileall backend api agents services database risk_engine tools workflows`
- Smoke test script: `bash scripts/smoke_test.sh http://localhost:8000`
