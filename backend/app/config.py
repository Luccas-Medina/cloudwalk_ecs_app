# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"  # fallback for local dev
)

class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    secret_key: str
    basic_auth_user: str
    basic_auth_pass: str
    log_level: str = "INFO"
    ingest_token: str | None = None
    app_name: str = "Empathic Credit System API"
    model_config = SettingsConfigDict(
        extra="allow", 
        env_file=".env",
        case_sensitive=False  # This allows INGEST_TOKEN to match ingest_token
    )

settings = Settings()