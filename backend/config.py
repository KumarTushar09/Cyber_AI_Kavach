import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Cyber AI Kavach API")
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://<INSTANCE1_PUBLIC_IP>:3000")

    USE_MCP = os.getenv("USE_MCP", "false").strip().lower() == "true"
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "")
    MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")
    MCP_GATEWAY_PATH = os.getenv("MCP_GATEWAY_PATH", "")
    MCP_GATEWAY_TIMEOUT_SECONDS = float(os.getenv("MCP_GATEWAY_TIMEOUT_SECONDS", "600"))
    MCP_TIMEOUT_CHAT_SECONDS = float(os.getenv("MCP_TIMEOUT_CHAT_SECONDS", "600"))
    MCP_TIMEOUT_EMBED_SECONDS = float(os.getenv("MCP_TIMEOUT_EMBED_SECONDS", "60"))
    MCP_TIMEOUT_PG_QUERY_SECONDS = float(os.getenv("MCP_TIMEOUT_PG_QUERY_SECONDS", "15"))
    MCP_TIMEOUT_QDRANT_SECONDS = float(os.getenv("MCP_TIMEOUT_QDRANT_SECONDS", "15"))
    MCP_TIMEOUT_S3_SECONDS = float(os.getenv("MCP_TIMEOUT_S3_SECONDS", "30"))
    MCP_TIMEOUT_HEALTH_SECONDS = float(os.getenv("MCP_TIMEOUT_HEALTH_SECONDS", "5"))

    # Local Ollama endpoint (Instance 2) for llama3.1:8b
    LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL") or os.getenv("LLM_ROUTER_BASE_URL", "http://172.31.19.31:11434")
    LLM_ANALYZE_PATH = os.getenv("LLM_ANALYZE_PATH", "/api/generate")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    QDRANT_HOST = os.getenv("QDRANT_HOST", "")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

    POSTGRES_DB = os.getenv("POSTGRES_DB", "")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

    QDRANT_COLLECTION_THREATS = os.getenv("QDRANT_COLLECTION_THREATS", "threat_vectors")

    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    AUTH_HEADER_NAME = os.getenv("AUTH_HEADER_NAME", "X-API-Key")
    API_KEY = os.getenv("API_KEY", "")
    API_KEY_SCOPES = os.getenv(
        "API_KEY_SCOPES",
        "analysis:read,knowledge:read,fraud:write,upload:write,system:read",
    )
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").strip().lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_BASE_DELAY_SECONDS = float(os.getenv("RETRY_BASE_DELAY_SECONDS", "0.5"))

    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
    SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
    SARVAM_AUTH_HEADER = os.getenv("SARVAM_AUTH_HEADER", "Authorization")
    SARVAM_AUTH_SCHEME = os.getenv("SARVAM_AUTH_SCHEME", "Bearer")

    SARVAM_STT_PATH = os.getenv("SARVAM_STT_PATH", "/speech-to-text")
    SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "")
    SARVAM_STT_LANGUAGE = os.getenv("SARVAM_STT_LANGUAGE", "en")

    SARVAM_TTS_PATH = os.getenv("SARVAM_TTS_PATH", "/text-to-speech")
    SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "")
    SARVAM_TTS_LANGUAGE = os.getenv("SARVAM_TTS_LANGUAGE", "en-IN")
    SARVAM_TTS_VOICE = os.getenv("SARVAM_TTS_VOICE", "")
    SARVAM_TTS_FORMAT = os.getenv("SARVAM_TTS_FORMAT", "mp3")

    SARVAM_EMBED_PATH = os.getenv("SARVAM_EMBED_PATH", "/embeddings")
    SARVAM_EMBED_MODEL = os.getenv("SARVAM_EMBED_MODEL", "")

    SARVAM_TIMEOUT_SECONDS = float(os.getenv("SARVAM_TIMEOUT_SECONDS", "60"))

    RAG_VECTOR_TABLE = os.getenv("RAG_VECTOR_TABLE", "knowledge_chunks")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.2"))
    RAG_QUERY_CHUNK_SIZE = int(os.getenv("RAG_QUERY_CHUNK_SIZE", "220"))
    RAG_QUERY_CHUNK_OVERLAP = int(os.getenv("RAG_QUERY_CHUNK_OVERLAP", "40"))
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))


settings = Settings()
