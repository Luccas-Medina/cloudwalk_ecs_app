# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    secret_key: str
    basic_auth_user: str
    basic_auth_pass: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()