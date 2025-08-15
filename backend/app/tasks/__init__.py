# Import all tasks to ensure they're registered with Celery
from .credit import evaluate_credit
from .emotion_ingest import persist_emotion_event
from .example import *