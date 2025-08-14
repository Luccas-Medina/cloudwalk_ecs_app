from celery import Celery
import os

# Broker and backend URLs from environment variables or defaults
broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

celery_app = Celery(
    "ecs_tasks",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.example"]  # Ensure tasks.py is in the same directory or package
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
