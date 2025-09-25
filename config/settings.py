from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database Credentials
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()