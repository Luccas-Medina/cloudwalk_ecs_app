# app/services/credit_deployment.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy.orm import Session
from app.credit_models.credit_deployment import (
    CreditOffer, CreditDeploymentEvent, CreditNotification, 
    UserCreditProfile, CreditOfferStatus, NotificationStatus
)
from app.core.database import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CreditDeploymentService:
    """Service for managing credit offer deployment lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_credit_offer(self, 
                          user_id: int,
                          offered_limit: float,
                          interest_rate: float,
                          model_version: str,
                          risk_assessment: Dict[str, Any],
                          emotional_context: Optional[Dict[str, Any]] = None,
                          expires_in_hours: int = 72) -> CreditOffer:
        """Create a new credit offer for user acceptance"""
        
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        offer = CreditOffer(
            user_id=user_id,
            offered_limit=offered_limit,
            interest_rate=interest_rate,
            model_version=model_version,
            risk_assessment=risk_assessment,
            emotional_context=emotional_context,
            expires_at=expires_at,
            status=CreditOfferStatus.PENDING
        )
        
        self.db.add(offer)
        self.db.commit()
        self.db.refresh(offer)
        
        # Log offer creation
        self._log_deployment_event(
            offer.id, user_id, "offer_created",
            {"offered_limit": offered_limit, "expires_at": expires_at.isoformat()},
            success=True
        )
        
        # Schedule notification
        self._create_notification(
            offer.id, user_id, "offer_ready",
            "New Credit Offer Available! 💳",
            f"You've been pre-approved for a credit limit of ${offered_limit:,.2f}. "
            f"Review and accept your offer before it expires.",
            deep_link=f"cloudwalk://credit/offer/{offer.id}"
        )
        
        logger.info(f"Created credit offer {offer.id} for user {user_id}: ${offered_limit}")
        return offer
    
    def accept_credit_offer(self, offer_id: int, user_id: int) -> Dict[str, Any]:
        """Process credit offer acceptance and trigger deployment"""
        
        offer = self.db.query(CreditOffer).filter(
            CreditOffer.id == offer_id,
            CreditOffer.user_id == user_id,
            CreditOffer.status == CreditOfferStatus.PENDING
        ).first()
        
        if not offer:
            raise ValueError("Credit offer not found or not available for acceptance")
        
        if offer.expires_at < datetime.utcnow():
            offer.status = CreditOfferStatus.EXPIRED
            self.db.commit()
            raise ValueError("Credit offer has expired")
        
        # Update offer status
        offer.status = CreditOfferStatus.ACCEPTED
        offer.accepted_at = datetime.utcnow()
        
        # Generate deployment task ID
        task_id = f"deploy_{offer_id}_{uuid.uuid4().hex[:8]}"
        offer.deployment_task_id = task_id
        
        self.db.commit()
        
        # Log acceptance
        self._log_deployment_event(
            offer.id, user_id, "offer_accepted",
            {"accepted_at": offer.accepted_at.isoformat(), "task_id": task_id},
            success=True
        )
        
        logger.info(f"Credit offer {offer_id} accepted by user {user_id}")
        
        return {
            "offer_id": offer_id,
            "task_id": task_id,
            "status": "accepted",
            "deployment_scheduled": True,
            "message": "Your credit offer has been accepted and is being deployed to your account."
        }
    
    def deploy_credit_to_account(self, offer_id: int, task_id: str) -> Dict[str, Any]:
        """Deploy accepted credit offer to user account (background task)"""
        start_time = datetime.utcnow()
        
        try:
            offer = self.db.query(CreditOffer).filter(
                CreditOffer.id == offer_id,
                CreditOffer.deployment_task_id == task_id,
                CreditOffer.status == CreditOfferStatus.ACCEPTED
            ).first()
            
            if not offer:
                raise ValueError(f"Credit offer {offer_id} not found for deployment")
            
            # Get or create user credit profile
            profile = self.db.query(UserCreditProfile).filter(
                UserCreditProfile.user_id == offer.user_id
            ).first()
            
            if not profile:
                profile = UserCreditProfile(
                    user_id=offer.user_id,
                    current_limit=0.0,
                    available_credit=0.0,
                    used_credit=0.0
                )
                self.db.add(profile)
            
            # Update credit profile with new limits
            old_limit = profile.current_limit
            profile.current_limit = offer.offered_limit
            profile.available_credit = offer.offered_limit - profile.used_credit
            profile.current_interest_rate = offer.interest_rate
            profile.last_limit_increase = datetime.utcnow()
            
            # Apply emotional intelligence insights if available
            if offer.emotional_context:
                profile.emotional_stability_score = offer.emotional_context.get('stability_score')
                profile.stress_indicators = offer.emotional_context.get('stress_patterns')
                profile.last_emotion_update = datetime.utcnow()
            
            # Update offer status
            offer.status = CreditOfferStatus.DEPLOYED
            offer.deployed_at = datetime.utcnow()
            offer.deployment_attempts += 1
            
            self.db.commit()
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Log successful deployment
            self._log_deployment_event(
                offer.id, offer.user_id, "credit_deployed",
                {
                    "old_limit": old_limit,
                    "new_limit": offer.offered_limit,
                    "increase": offer.offered_limit - old_limit,
                    "processing_time_ms": processing_time
                },
                success=True,
                task_id=task_id,
                processing_time_ms=processing_time
            )
            
            # Send success notification
            self._create_notification(
                offer.id, offer.user_id, "credit_deployed",
                "Credit Limit Updated! 🎉",
                f"Your credit limit has been increased to ${offer.offered_limit:,.2f}. "
                f"Your new available credit is ${profile.available_credit:,.2f}.",
                deep_link=f"cloudwalk://credit/dashboard"
            )
            
            logger.info(f"Successfully deployed credit offer {offer_id} to user {offer.user_id}")
            
            return {
                "status": "deployed",
                "offer_id": offer_id,
                "user_id": offer.user_id,
                "new_limit": offer.offered_limit,
                "old_limit": old_limit,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            # Handle deployment failure
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            if 'offer' in locals():
                offer.deployment_attempts += 1
                offer.deployment_error = str(e)
                self.db.commit()
                
                # Log failure
                self._log_deployment_event(
                    offer.id, offer.user_id, "deployment_failed",
                    {"error": str(e), "attempt": offer.deployment_attempts},
                    success=False,
                    task_id=task_id,
                    processing_time_ms=processing_time
                )
                
                # Send failure notification
                self._create_notification(
                    offer.id, offer.user_id, "deployment_failed",
                    "Credit Deployment Issue",
                    "There was an issue processing your credit offer. "
                    "Our team has been notified and will resolve this shortly.",
                    deep_link=f"cloudwalk://support/contact"
                )
            
            logger.error(f"Failed to deploy credit offer {offer_id}: {e}")
            raise
    
    def get_user_credit_offers(self, user_id: int, status: Optional[str] = None) -> List[CreditOffer]:
        """Get credit offers for a user"""
        query = self.db.query(CreditOffer).filter(CreditOffer.user_id == user_id)
        
        if status:
            query = query.filter(CreditOffer.status == status)
        
        return query.order_by(CreditOffer.created_at.desc()).all()
    
    def get_deployment_history(self, offer_id: int) -> List[CreditDeploymentEvent]:
        """Get deployment event history for an offer"""
        return self.db.query(CreditDeploymentEvent).filter(
            CreditDeploymentEvent.offer_id == offer_id
        ).order_by(CreditDeploymentEvent.created_at.asc()).all()
    
    def _log_deployment_event(self, 
                            offer_id: int, 
                            user_id: int, 
                            event_type: str,
                            event_data: Dict[str, Any],
                            success: bool,
                            task_id: Optional[str] = None,
                            processing_time_ms: Optional[int] = None):
        """Log deployment event for audit trail"""
        
        event = CreditDeploymentEvent(
            offer_id=offer_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            task_id=task_id,
            processing_time_ms=processing_time_ms,
            success=success,
            processed_at=datetime.utcnow() if success else None
        )
        
        self.db.add(event)
        self.db.commit()
    
    def _create_notification(self,
                           offer_id: int,
                           user_id: int,
                           notification_type: str,
                           title: str,
                           message: str,
                           deep_link: Optional[str] = None):
        """Create notification for mobile app"""
        
        notification = CreditNotification(
            offer_id=offer_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            deep_link=deep_link,
            status=NotificationStatus.PENDING
        )
        
        self.db.add(notification)
        self.db.commit()
        
        logger.info(f"Created notification for user {user_id}: {title}")

class NotificationService:
    """Service for sending mobile push notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_push_notification(self, notification_id: int) -> Dict[str, Any]:
        """Send push notification to mobile device"""
        
        notification = self.db.query(CreditNotification).filter(
            CreditNotification.id == notification_id
        ).first()
        
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")
        
        try:
            # Simulate push notification sending
            # In real implementation, integrate with FCM/APNS
            push_id = f"push_{uuid.uuid4().hex[:12]}"
            
            # Mock successful delivery
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.push_notification_id = push_id
            notification.delivery_response = {
                "push_id": push_id,
                "status": "sent",
                "provider": "fcm" if notification.platform == "android" else "apns"
            }
            
            self.db.commit()
            
            logger.info(f"Sent push notification {push_id} to user {notification.user_id}")
            
            return {
                "notification_id": notification_id,
                "push_id": push_id,
                "status": "sent",
                "user_id": notification.user_id
            }
            
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.delivery_response = {"error": str(e)}
            self.db.commit()
            
            logger.error(f"Failed to send notification {notification_id}: {e}")
            raise
