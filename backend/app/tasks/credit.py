from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models import User, EmotionalEvent
from app.services.credit_service import calculate_credit_offer
from sqlalchemy import func

@shared_task(name="evaluate_credit_task")
def evaluate_credit(user_id: int):
    """
    Celery task to evaluate credit using integrated ML model.
    Uses the unified credit_service with proper ML integration.
    """
    db: Session = SessionLocal()
    try:
        # Debug: Check if User model is available
        if User is None:
            return {"status": "error", "message": "User model not available - import failed"}
        
        # Debug: Log the user lookup attempt
        print(f"Looking up user with ID: {user_id}")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Debug: Check if any users exist
            user_count = db.query(User).count()
            return {
                "status": "error", 
                "message": f"User {user_id} not found. Total users in DB: {user_count}",
                "debug_info": {"requested_user_id": user_id, "total_users": user_count}
            }

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
        return {
            "status": "error", 
            "message": str(e),
            "debug_info": {
                "requested_user_id": user_id,
                "exception_type": type(e).__name__
            }
        }
    finally:
        db.close()
