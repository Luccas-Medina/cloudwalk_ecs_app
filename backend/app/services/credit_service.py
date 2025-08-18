# app/services/credit_service.py
from app.ml.protected_model import get_protected_risk_score
from app.core.db import SessionLocal
from app.models import Transaction, EmotionalEvent, User
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

def calculate_credit_offer(user_id: int):
    db = SessionLocal()
    try:
        # Financial data
        transactions = db.query(Transaction).filter_by(user_id=user_id).all()
        transaction_count = len(transactions)
        avg_amount = sum(t.amount for t in transactions) / transaction_count if transactions else 0

        user = db.query(User).get(user_id)
        current_limit = user.credit_limit if user else 0

        # Emotional data
        avg_valence, avg_arousal = db.query(
            func.avg(EmotionalEvent.valence),
            func.avg(EmotionalEvent.arousal)
        ).filter_by(user_id=user_id).first()

        last_emotion = db.query(EmotionalEvent.emotion_label)\
                         .filter_by(user_id=user_id)\
                         .order_by(EmotionalEvent.timestamp.desc())\
                         .first()
        last_emotion = last_emotion[0] if last_emotion else None

        # Prepare features for ML model
        features = {
            "transaction_count": transaction_count,
            "avg_transaction_amount": avg_amount,
            "current_credit_limit": current_limit,
            "avg_valence": avg_valence or 0,
            "avg_arousal": avg_arousal or 0,
            "last_emotion": last_emotion
        }

        # Call protected ML model with circuit breaker protection
        ml_result = get_protected_risk_score(features)
        risk_score = ml_result['risk_score']
        
        # Log prediction source for monitoring
        logger.info(f"Credit risk prediction from {ml_result['prediction_source']} "
                   f"(circuit breaker: {ml_result['circuit_breaker_state']}) "
                   f"for user {user_id}: {risk_score}")

        # Integrate ML model output into credit limit calculation
        approved = risk_score < 0.6  # Threshold for approval
        
        # Calculate new credit limit based on risk score
        if approved:
            # Lower risk = higher limit increase
            risk_factor = 1 - risk_score  # Convert to positive factor (0.4 to 1.0)
            limit_multiplier = 1.0 + (risk_factor * 0.5)  # 1.0 to 1.5x increase
            new_limit = current_limit * limit_multiplier
        else:
            new_limit = current_limit  # No increase for high risk
        
        # Risk-based interest rate
        base_rate = 0.15
        risk_premium = risk_score * 0.10  # 0-10% additional rate based on risk
        interest_rate = base_rate + risk_premium
        
        # Determine credit type based on risk score and emotional stability
        if approved:
            if risk_score < 0.3:
                credit_type = "Long-Term"  # Low risk = Long-term credit
            elif risk_score < 0.6:
                # Check emotional stability for medium risk
                if avg_arousal and avg_arousal < 0.4:  # Low arousal = emotionally stable
                    credit_type = "Long-Term"
                else:
                    credit_type = "Short-Term"
            else:
                credit_type = "Short-Term"  # Higher risk = Short-term only
        else:
            credit_type = "Rejected"

        return {
            "approved": approved,
            "risk_score": risk_score,
            "new_credit_limit": round(new_limit, 2),
            "interest_rate": round(interest_rate, 4),
            "credit_type": credit_type,
            "features_used": features,
            "ml_model_info": {
                "model_version": ml_result['model_version'],
                "prediction_source": ml_result['prediction_source'],
                "circuit_breaker_state": ml_result['circuit_breaker_state'],
                "response_time": ml_result['response_time']
            }
        }
    finally:
        db.close()
