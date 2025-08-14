from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"

settings = Settings()
