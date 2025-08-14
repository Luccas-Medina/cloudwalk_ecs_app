from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    app_host: str
    app_port: int
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_pass: str
    redis_host: str
    redis_port: int
    celery_broker_url: str
    celery_result_backend: str
    database_url: str
    rabbitmq_url: str
    secret_key: str
    basic_auth_user: str
    basic_auth_pass: str

    model_config = SettingsConfigDict(extra="allow", env_file=".env")

settings = Settings()
