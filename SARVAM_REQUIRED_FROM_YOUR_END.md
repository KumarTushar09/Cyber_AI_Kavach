# Sarvam + ShaktiDB Inputs Required From Your End

This checklist contains the exact values needed to run the new voice-first RAG pipeline.

## 1) Sarvam API
- SARVAM_API_KEY: provide production key.
- SARVAM_BASE_URL: set to `https://api.sarvam.ai` (standard default applied).
- SARVAM_AUTH_HEADER: set to `Authorization` (standard default applied).
- SARVAM_AUTH_SCHEME: set to `Bearer` (standard default applied).

## 2) Sarvam STT (Speech-to-Text)
- SARVAM_STT_PATH: API path for transcription.
- SARVAM_STT_MODEL: model name.
- SARVAM_STT_LANGUAGE: language code (default: en).
- Confirm accepted upload field name is `file` (or share required field name).
- Confirm max audio size and max duration.

## 3) Sarvam Embeddings
- SARVAM_EMBED_PATH: API path for embeddings.
- SARVAM_EMBED_MODEL: embedding model name.
- EMBEDDING_DIMENSION: vector dimension from model output.
- Confirm response field that contains embedding array.

## 4) ShaktiDB (Postgres + pgvector)
- Status: completed.
- pgvector extension is enabled.
- Vector table is created: knowledge_chunks.
- Current schema is available:
  - id (BIGSERIAL PRIMARY KEY)
  - source (TEXT)
  - chunk (TEXT)
  - metadata (JSONB)
  - embedding (vector(1536))
  - created_at (TIMESTAMPTZ)
- Indexes created:
  - idx_knowledge_chunks_embedding_cosine (ivfflat, vector_cosine_ops)
  - idx_knowledge_chunks_source
  - idx_knowledge_chunks_metadata_gin
- Cosine search operator is available using pgvector `<=>`.

Note:
- If test vectors are all zeros, cosine score can be NaN. Use non-zero embeddings for validation queries.

## 5) S3 Knowledge Source
- S3 bucket name: `cyber-ai-kavach-storage`
- Prefix path: `s3://cyber-ai-kavach-storage/Knowledge_based_data/`
- Allowed file types: `.pdf`, `.txt`, `.docx`
- Re-index schedule: `manual`
- Max file size per object: `10 MB`
- Max objects per run: `100`

Where to update later if these values change:
- `REQUIRED_FROM_YOUR_END.md` under section `## 6) S3 Knowledge Source`
- `SARVAM_REQUIRED_FROM_YOUR_END.md` under section `## 6) S3 Knowledge Source`
- `backend/.env` for runtime bucket-level configuration values

## 6) Product Behavior
- Supported languages for voice assistant: `en-IN` for now.
- Max recording duration for frontend mic capture: `60 seconds`.
- Transcript visibility rule: `always show transcript in chat before assistant answer`.
- STT failure fallback behavior: `show clear error and instruct user to type question in text input`.

## 7) Security and Rate Limits
- Confirm voice endpoint scope policy (currently uses knowledge:read).
- Rate limit target for voice endpoint.
- Audio/transcript retention policy and log redaction expectations.

## 8) Environment Variables To Add In backend/.env
- SARVAM_API_KEY=
- SARVAM_BASE_URL=https://api.sarvam.ai
- SARVAM_AUTH_HEADER=Authorization
- SARVAM_AUTH_SCHEME=Bearer
- SARVAM_STT_PATH=/speech-to-text
- SARVAM_STT_MODEL=
- SARVAM_STT_LANGUAGE=en
- SARVAM_EMBED_PATH=/embeddings
- SARVAM_EMBED_MODEL=
- SARVAM_TIMEOUT_SECONDS=60
- RAG_VECTOR_TABLE=knowledge_chunks
- RAG_TOP_K=5
- RAG_MIN_SIMILARITY=0.2
- RAG_QUERY_CHUNK_SIZE=220
- RAG_QUERY_CHUNK_OVERLAP=40
- EMBEDDING_DIMENSION=1536

## 9) Remaining Required From Your Side (Pending)
- Sarvam API contract details for STT/Embeddings (exact paths, models, and response fields).
- Final values for all SARVAM_* env vars.
- S3 document prefixes and file types for knowledge ingestion.
- Voice product limits (max duration, languages, transcript visibility, STT fallback behavior).
