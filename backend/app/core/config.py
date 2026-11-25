"""Application settings for HealthBuddy v3.0."""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
CLINICAL_DATA_DIR = DATA_DIR / "clinical"
CARE_DATA_DIR = DATA_DIR / "care"
ARTIFACTS_DIR = BACKEND_DIR / "artifacts"


class Settings(BaseSettings):
    APP_NAME: str = "HealthBuddy"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'healthbuddy.db').as_posix()}"
    JWT_SECRET_KEY: str = "healthbuddy-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3005,http://127.0.0.1:3005,http://localhost:3006,http://127.0.0.1:3006"
    ML_LOW_THRESHOLD: float = 0.10
    ML_HIGH_THRESHOLD: float = 0.30

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = str(REPO_ROOT / ".env")
        extra = "ignore"


settings = Settings()

