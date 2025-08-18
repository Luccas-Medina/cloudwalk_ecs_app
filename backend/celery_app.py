from celery import Celery
import os

# Broker and backend URLs from environment variables or defaults
broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

celery_app = Celery(
    "ecs_tasks",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.example", 
        "app.tasks.credit", 
        "app.tasks.emotion_ingest",
        "app.tasks.credit_deployment"  # Re-enabled with fixed imports
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    
    # Task routing for different queues
    task_routes={
        "app.tasks.emotion_ingest.*": {"queue": "emotion_processing"},
        "app.tasks.credit_deployment.*": {"queue": "credit_deployment"},
        "app.tasks.credit.*": {"queue": "credit_processing"},
        "app.tasks.example.*": {"queue": "default"},
    },
    
    # Task execution settings
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Periodic task configuration (requires celery beat)
    beat_schedule={
        "process-credit-offer-expiry": {
            "task": "app.tasks.credit_deployment.process_credit_offer_expiry",
            "schedule": 3600.0,  # Every hour
        },
    },
)
