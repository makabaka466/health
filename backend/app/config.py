import os
from typing import Optional


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    DB_NAME: str = os.getenv("DB_NAME", "health")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    )

    # JWT 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 初始管理员账号
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@health.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_REGISTER_KEY: str = os.getenv("ADMIN_REGISTER_KEY", "123")

    # API 配置
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "健康管理系统"

    # Ollama / 本地大模型配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    OLLAMA_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
    OLLAMA_TOP_P: float = float(os.getenv("OLLAMA_TOP_P", "0.8"))
    OLLAMA_TOP_K: int = int(os.getenv("OLLAMA_TOP_K", "20"))
    OLLAMA_REPEAT_PENALTY: float = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
    OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "1024"))
    OLLAMA_DISABLE_THINKING: bool = _env_bool("OLLAMA_DISABLE_THINKING", True)
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_EMBEDDING_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_EMBEDDING_TIMEOUT_SECONDS", "120"))

    # RAG 配置
    AI_RAG_LIMIT: int = int(os.getenv("AI_RAG_LIMIT", "3"))
    AI_CHAT_HISTORY_LIMIT: int = int(os.getenv("AI_CHAT_HISTORY_LIMIT", "3"))
    RAG_VECTOR_ENABLED: bool = _env_bool("RAG_VECTOR_ENABLED", True)
    RAG_VECTOR_COLLECTION: str = os.getenv("RAG_VECTOR_COLLECTION", "health_rag_documents")
    RAG_VECTOR_BASE_URL: str = os.getenv("RAG_VECTOR_BASE_URL", "http://127.0.0.1:6333")
    RAG_VECTOR_TIMEOUT_SECONDS: int = int(os.getenv("RAG_VECTOR_TIMEOUT_SECONDS", "30"))
    RAG_VECTOR_TOP_K: int = int(os.getenv("RAG_VECTOR_TOP_K", "6"))
    RAG_VECTOR_SCORE_THRESHOLD: float = float(os.getenv("RAG_VECTOR_SCORE_THRESHOLD", "0.15"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "80"))

    # 链上配置（Ganache / EVM）
    WEB3_PROVIDER_URI: str = os.getenv("WEB3_PROVIDER_URI", "http://127.0.0.1:7545")
    HEALTH_DATA_CONTRACT_ADDRESS: Optional[str] = os.getenv("HEALTH_DATA_CONTRACT_ADDRESS")
    HEALTH_DATA_CONTRACT_ABI_JSON: Optional[str] = os.getenv("HEALTH_DATA_CONTRACT_ABI_JSON")

    # 跨域配置
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]


settings = Settings()
