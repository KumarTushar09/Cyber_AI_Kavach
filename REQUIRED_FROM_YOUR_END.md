# Required Inputs From Your End

This project is currently set to run safely without external integrations.
When you are ready, share the values below and I will wire them immediately.

## MCP Gateway (Current Cutover Path)
- Status: pending final activation from your side
- MCP_SERVER_URL: http://172.31.19.31:9000
- Auth header: Authorization: Bearer <MCP_AUTH_TOKEN>
- Token rotation: every 30 days (or immediately after incident)
- Tool timeout expectations:
	- chat: 600 seconds
	- embed: 60 seconds
	- pg_query: 15 seconds
	- qdrant_search: 15 seconds
	- s3_get_put: 30 seconds
	- health: 5 seconds
	- gateway hard cap: 600 seconds

### Required Before Enabling USE_MCP=true
- Provide MCP_AUTH_TOKEN securely for Instance 1 backend env.
- Open security group route Instance 1 -> Instance 2 on TCP 9000.
- Keep Instance 2 -> Instance 3 routes open:
	- TCP 15234 (Postgres)
	- TCP 6333 (Qdrant)
- Ensure Instance 2 can reach S3 over HTTPS 443 via VPC endpoint or NAT.
- Confirm pg_query allowlist IDs remain:
	- knowledge_similarity_search
	- indicator_lookup
	- knowledge_chunk_by_id
	- health_ping
- Confirm S3 IAM prefix policy:
	- read-only: Knowledge_based_data/
	- read-write: artifacts/
	- read-write: reports/

### Instance 1 Activation Steps
- Set MCP_AUTH_TOKEN in backend/.env.
- Set USE_MCP=true in backend/.env.
- Restart backend container via docker compose.
- Run smoke script for /health, /api/v1/analyze/url, /api/v1/knowledge/query, /api/v1/system/readiness.

## 1) Instance 2 (LLM Router)
- Status: completed
- LLM router base URL received: `http://172.31.19.31:8001`
- Confirmed variable name from your side: `LLM_ROUTER_BASE_URL`
- Router timeout received: `600`
- Ollama default model on Instance 2: `llama3.1:8b`

Notes:
- This backend now accepts either `LLM_ROUTER_URL` or `LLM_ROUTER_BASE_URL`, plus `LLM_TIMEOUT_SECONDS`.
- `OLLAMA_DEFAULT_MODEL` is managed on Instance 2 and is not consumed directly by the current Instance 1 backend code.

## 2) Instance 3 (Postgres)
- Status: configured and reachable
- POSTGRES_HOST: `172.31.31.76`
- POSTGRES_PORT: `15234`
- POSTGRES_DB: `postgres`
- POSTGRES_USER: `postgres`
- POSTGRES_PASSWORD: received

## 3) Instance 3 (Qdrant)
- Status: configured and reachable
- QDRANT_HOST: `172.31.31.76`
- QDRANT_PORT: `6333`
- QDRANT_COLLECTION_THREATS: `threat_vectors`
- Verified after fix:
	- Qdrant now maps `0.0.0.0:6333-6334->6333-6334/tcp`
	- Instance 1 can reach `172.31.31.76:6333`
	- `GET /collections` returns status `ok`

## 4) S3 Upload
- Status: **completed and verified**
- AWS_REGION: `ap-south-2`
- S3_BUCKET_NAME: `cyber-ai-kavach-storage`
- IAM role `cyber-ai-kavach-s3-role` attached to Instance 1 and confirmed working
- boto3 v1.35.36 already installed in Python environment
- Live check: `head_bucket` passed — bucket is accessible from Instance 1

## 6) S3 Knowledge Source
- Status: configured
- S3 bucket name: `cyber-ai-kavach-storage`
- Prefix path for knowledge ingestion: `s3://cyber-ai-kavach-storage/Knowledge_based_data/`
- Allowed file types: `.pdf`, `.txt`, `.docx`
- Re-index schedule: `manual`
- Max file size per object: `10 MB`
- Max objects per run: `100`

## 5) Network/Access Checks
- Instance 1 can reach Instance 2 on LLM router port
- Instance 1 can reach Instance 3 Postgres port (`172.31.31.76:15234`) - verified open
- Instance 1 can reach Instance 3 Qdrant port (`172.31.31.76:6333`) - verified open
- IAM/credentials allow upload to the S3 bucket
- If Postgres and Qdrant run on the same Instance 3 EC2, both `POSTGRES_HOST` and `QDRANT_HOST` should be that EC2's private IP.

## Where These Go
- Environment template: `backend/.env`

## Current Status
- Instance 2 LLM router: **done**
- S3 bucket + IAM role: **done and verified**
- Postgres (Instance 3): **configured and reachable on 15234**
- Qdrant (Instance 3): **configured and reachable on 6333**
- Core external dependencies are now reachable from Instance 1.
