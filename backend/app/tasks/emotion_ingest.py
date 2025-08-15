from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.core.db import SessionLocal
from app.models import EmotionalEvent
import dateutil.parser as dtparse  # add python-dateutil to requirements if not present

@shared_task(bind=True, name="persist_emotion_event", max_retries=3, default_retry_delay=2)
def persist_emotion_event(self, event: dict):
    """
    Persist a normalized emotion event into the database.
    Retries on transient DB errors.
    """
    db: Session = SessionLocal()
    try:
        ts = event.get("timestamp")
        ev_ts = None
        if ts:
            try:
                ev_ts = dtparse.parse(ts)  # tolerate ISO strings
            except Exception:
                ev_ts = None

        row = EmotionalEvent(
            user_id=event["user_id"],
            session_id=event.get("session_id"),
            source=event.get("source"),
            emotion_label=event.get("emotion_label"),
            valence=event.get("valence"),
            arousal=event.get("arousal"),
            confidence=event.get("confidence"),
            raw_payload=event.get("raw_payload"),
            timestamp=ev_ts,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"status": "ok", "id": row.id}
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "error": str(exc)}
    finally:
        db.close()
