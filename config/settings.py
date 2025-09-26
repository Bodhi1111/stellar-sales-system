from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database Credentials
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # LLM Settings
    OLLAMA_API_URL: str = "http://localhost:11434/api/generate"
    LLM_MODEL_NAME: str = "mistral"

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    # Agent-Specific Settings
    WATCHER_DIRECTORY: Path = BASE_DIR / "data" / "transcripts"
    
    # Vector DB Settings
    QDRANT_URL: str = "http://localhost:6333"

    # Embedding Model Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()