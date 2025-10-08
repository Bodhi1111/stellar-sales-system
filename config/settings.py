from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # PostgreSQL Database Credentials
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # LLM Settings
    OLLAMA_API_URL: str
    LLM_MODEL_NAME: str

    # Vector DB Settings
    QDRANT_URL: str

    # Embedding Model Settings
    EMBEDDING_MODEL_NAME: str

    # Neo4j Settings
    NEO4J_URL: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Baserow Settings
    BASEROW_URL: str
    BASEROW_TOKEN: str
    BASEROW_DATABASE_ID: int
    BASEROW_CLIENTS_ID: int
    BASEROW_MEETINGS_ID: int
    BASEROW_DEALS_ID: int
    BASEROW_COMMUNICATIONS_ID: int
    BASEROW_SALES_COACHING_ID: int

    # Computed Properties (derived from file location, not from .env)
    @property
    def BASE_DIR(self) -> Path:
        """Project root directory"""
        return Path(__file__).resolve().parent.parent

    @property
    def WATCHER_DIRECTORY(self) -> Path:
        """Directory to watch for new transcripts"""
        return self.BASE_DIR / "data" / "transcripts"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()