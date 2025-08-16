# app/tasks/credit_deployment.py
from celery import shared_task
from app.services.credit_deployment import CreditDeploymentService, NotificationService
from app.core.database import SessionLocal  # Use SessionLocal instead
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deploy_credit_to_account(self, offer_id: int, task_id: str) -> Dict[str, Any]:
    """
    Background task to deploy accepted credit offer to user account
    
    This task:
    1. Updates user's credit profile in database
    2. Applies new credit limits
    3. Logs deployment events for audit trail
    4. Triggers success/failure notifications
    """
    db = SessionLocal()
    try:
        service = CreditDeploymentService(db)
        
        logger.info(f"Starting credit deployment for offer {offer_id} (task: {task_id})")
        
        # Deploy credit to user account
        result = service.deploy_credit_to_account(offer_id, task_id)
        
        # Schedule notification task
        send_credit_notification.delay(
            user_id=result["user_id"],
            notification_type="credit_deployed",
            title="Credit Limit Updated! 🎉",
            message=f"Your credit limit has been increased to ${result['new_limit']:,.2f}.",
            metadata={"offer_id": offer_id, "deployment_task_id": task_id}
        )
        
        logger.info(f"Successfully deployed credit offer {offer_id}")
        return result
        
    except Exception as e:
        logger.error(f"Credit deployment failed for offer {offer_id}: {e}")
        
        # Schedule failure notification
        send_credit_notification.delay(
            user_id=offer_id,  # We'll extract from offer in the notification task
            notification_type="deployment_failed",
            title="Credit Deployment Issue",
            message="There was an issue processing your credit offer. Our team has been notified.",
            metadata={"offer_id": offer_id, "error": str(e)}
        )
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying credit deployment for offer {offer_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise
    finally:
        db.close()

@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_credit_notification(self, 
                           user_id: int, 
                           notification_type: str,
                           title: str, 
                           message: str,
                           metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Background task to send push notifications to mobile app
    
    Handles:
    1. Push notification delivery via FCM/APNS
    2. Delivery confirmation tracking
    3. Retry logic for failed deliveries
    4. Deep linking for in-app navigation
    """
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        
        # Create notification record
        from app.credit_models.credit_deployment import CreditNotification, NotificationStatus
        notification = CreditNotification(
            offer_id=metadata.get("offer_id") if metadata else None,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            deep_link=_generate_deep_link(notification_type, metadata),
            status=NotificationStatus.PENDING
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send push notification
        result = notification_service.send_push_notification(notification.id)
        
        logger.info(f"Successfully sent notification {notification.id} to user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying notification for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        raise
    finally:
        db.close()

@shared_task
def process_credit_offer_expiry() -> Dict[str, Any]:
    """
    Periodic task to check and expire old credit offers
    
    Runs every hour to:
    1. Mark expired offers as EXPIRED
    2. Clean up pending deployment tasks
    3. Send expiry notifications
    """
    db = SessionLocal()
    try:
        service = CreditDeploymentService(db)
        
        from app.credit_models.credit_deployment import CreditOffer, CreditOfferStatus
        from datetime import datetime
        
        # Find expired offers
        expired_offers = db.query(CreditOffer).filter(
            CreditOffer.expires_at < datetime.utcnow(),
            CreditOffer.status == CreditOfferStatus.PENDING
        ).all()
        
        results = []
        
        for offer in expired_offers:
            # Update status
            offer.status = CreditOfferStatus.EXPIRED
            
            # Log expiry event
            service._log_deployment_event(
                offer.id, offer.user_id, "offer_expired",
                {"expired_at": datetime.utcnow().isoformat()},
                success=True
            )
            
            # Send expiry notification
            send_credit_notification.delay(
                user_id=offer.user_id,
                notification_type="offer_expired",
                title="Credit Offer Expired",
                message=f"Your credit offer of ${offer.offered_limit:,.2f} has expired. Apply again to get a new offer.",
                metadata={"offer_id": offer.id}
            )
            
            results.append({
                "offer_id": offer.id,
                "user_id": offer.user_id,
                "offered_limit": offer.offered_limit,
                "expired_at": datetime.utcnow().isoformat()
            })
        
        db.commit()
        
        logger.info(f"Processed {len(expired_offers)} expired credit offers")
        
        return {
            "processed_count": len(expired_offers),
            "expired_offers": results
        }
        
    except Exception as e:
        logger.error(f"Failed to process credit offer expiry: {e}")
        raise
    finally:
        db.close()

@shared_task
def update_emotional_credit_insights(user_id: int, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to update user credit profile with emotional intelligence insights
    
    Called when significant emotional patterns are detected:
    1. High stress levels -> May indicate financial pressure
    2. Positive emotional trends -> May support credit increases
    3. Emotional instability -> May require more conservative limits
    """
    db = SessionLocal()
    try:
        
        from app.credit_models.credit_deployment import UserCreditProfile
        
        profile = db.query(UserCreditProfile).filter(
            UserCreditProfile.user_id == user_id
        ).first()
        
        if not profile:
            logger.warning(f"No credit profile found for user {user_id}")
            return {"status": "no_profile", "user_id": user_id}
        
        # Update emotional insights
        profile.emotional_stability_score = emotion_data.get("stability_score")
        profile.stress_indicators = emotion_data.get("stress_patterns")
        profile.last_emotion_update = datetime.utcnow()
        
        # Assess risk based on emotional patterns
        if emotion_data.get("high_stress_detected"):
            logger.info(f"High stress detected for user {user_id}, updating risk assessment")
            
            # Could trigger credit limit review or enhanced monitoring
            send_credit_notification.delay(
                user_id=user_id,
                notification_type="wellness_check",
                title="Financial Wellness Check",
                message="We've noticed you might be experiencing some stress. "
                        "Our support team is here to help with your financial goals.",
                metadata={"emotion_trigger": "high_stress"}
            )
        
        db.commit()
        
        logger.info(f"Updated emotional insights for user {user_id}")
        
        return {
            "status": "updated",
            "user_id": user_id,
            "stability_score": emotion_data.get("stability_score"),
            "last_update": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update emotional insights for user {user_id}: {e}")
        raise
    finally:
        db.close()

def _generate_deep_link(notification_type: str, metadata: Dict[str, Any] = None) -> str:
    """Generate deep link for mobile app navigation"""
    
    if notification_type == "offer_ready":
        return f"cloudwalk://credit/offer/{metadata.get('offer_id')}"
    elif notification_type == "credit_deployed":
        return "cloudwalk://credit/dashboard"
    elif notification_type == "deployment_failed":
        return "cloudwalk://support/contact"
    elif notification_type == "offer_expired":
        return "cloudwalk://credit/apply"
    elif notification_type == "wellness_check":
        return "cloudwalk://support/wellness"
    else:
        return "cloudwalk://home"

# Periodic task configuration should be done in celery_app.py
# using the main celery app instance
