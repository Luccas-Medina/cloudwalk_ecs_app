from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models import User
from app.services.credit_service import calculate_credit_offer
from sqlalchemy import func
from app.models import EmotionalEvent

@shared_task(name="evaluate_credit_task")
def evaluate_credit(user_id: int):
    """
    Celery task to evaluate credit using integrated ML model.
    Uses the unified credit_service with proper ML integration.
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}

        # Use the integrated credit service with ML model
        credit_result = calculate_credit_offer(user_id)

        # Update user with new credit information
        if credit_result["approved"]:
            user.credit_limit = credit_result["new_credit_limit"]
            user.credit_type = credit_result["credit_type"]
            db.commit()

        return {
            "user_id": user.id,
            "status": "success", 
            "credit_evaluation": credit_result,
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
