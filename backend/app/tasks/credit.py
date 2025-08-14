from celery import shared_task
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models import User

def mock_ml_credit_score(user_data: dict) -> float:
    """
    Mock function to simulate ML model.
    Returns a risk score between 0 (low risk) and 1 (high risk).
    """
    return random.random()


@shared_task(name="evaluate_credit_task")
def evaluate_credit(user_id: int):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}

        # Example: collect features from transactions and emotional events
        user_data = {
            "transaction_count": len(user.transactions),
            "average_transaction": sum([t.amount for t in user.transactions]) / (len(user.transactions) or 1),
            "emotion_events": len(user.emotional_events),
        }

        risk_score = mock_ml_credit_score(user_data)

        # Simple rule to calculate credit limit
        if risk_score < 0.3:
            credit_limit = 10000
            credit_type = "Long-Term"
        elif risk_score < 0.6:
            credit_limit = 5000
            credit_type = "Short-Term"
        else:
            credit_limit = 1000
            credit_type = "Short-Term"

        # Update user
        user.credit_limit = credit_limit
        user.credit_type = credit_type
        db.commit()

        return {
            "user_id": user.id,
            "risk_score": risk_score,
            "credit_limit": credit_limit,
            "credit_type": credit_type,
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
