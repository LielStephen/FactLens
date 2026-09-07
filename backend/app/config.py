import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "FactLens"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # LLM (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_MAX_TOKENS: int = 600
    GROQ_TEMPERATURE: float = 0.1

    # Supabase Credentials
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_BUCKET: str = "documents"

    # Database
    DATABASE_URL: Optional[str] = None

    # Processing limits & thresholds
    MAX_CANDIDATES_PER_PAGE: int = 15
    MAX_RELATIONSHIP_CANDIDATES: int = 8
    SIMILARITY_THRESHOLD: float = 0.65
    EVIDENCE_VALIDATION_MIN_SCORE: float = 0.70


settings = Settings()
