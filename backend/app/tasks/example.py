from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ecs_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

@celery_app.task
def add_numbers(a: int, b: int):
    return a + b
