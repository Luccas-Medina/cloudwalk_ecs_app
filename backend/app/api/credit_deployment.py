# app/api/credit_deployment.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from app.auth import basic_auth
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.services.credit_deployment import CreditDeploymentService, NotificationService
from app.tasks.credit_deployment import deploy_credit_to_account, send_credit_notification
from app.credit_models.credit_deployment import CreditOffer, CreditOfferStatus, CreditDeploymentEvent
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/credit", tags=["Credit Deployment"])

# Pydantic models for API
class CreditOfferCreate(BaseModel):
    user_id: int = Field(..., description="User ID", gt=0)
    offered_limit: float = Field(..., description="Offered credit limit", gt=0)
    interest_rate: float = Field(..., description="Interest rate", ge=0, le=1)
    model_version: str = Field(..., description="ML model version used")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment data")
    emotional_context: Optional[Dict[str, Any]] = Field(None, description="Emotional intelligence context")
    expires_in_hours: int = Field(72, description="Hours until offer expires", gt=0, le=168)

class CreditOfferResponse(BaseModel):
    id: int
    user_id: int
    offered_limit: float
    interest_rate: float
    status: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
    deployed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class OfferAcceptanceRequest(BaseModel):
    user_id: int = Field(..., description="User ID accepting the offer")
    terms_accepted: bool = Field(..., description="User has accepted terms and conditions")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information for notifications")

class OfferAcceptanceResponse(BaseModel):
    offer_id: int
    task_id: str
    status: str
    deployment_scheduled: bool
    message: str
    estimated_completion: Optional[str]

class DeploymentStatusResponse(BaseModel):
    offer_id: int
    status: str
    deployment_progress: str
    events: List[Dict[str, Any]]
    current_step: str
    estimated_completion: Optional[str]

class UserCreditSummary(BaseModel):
    user_id: int
    current_limit: float
    available_credit: float
    used_credit: float
    interest_rate: Optional[float]
    pending_offers: int
    last_limit_increase: Optional[datetime]
    emotional_stability_score: Optional[float]

@router.post("/offers", response_model=CreditOfferResponse, status_code=status.HTTP_201_CREATED)
def create_credit_offer(
    offer_data: CreditOfferCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """
    Create a new credit offer for a user
    
    This endpoint is typically called by the ML-powered credit evaluation system
    after determining a user is eligible for a credit increase.
    """
    try:
        service = CreditDeploymentService(db)
        
        offer = service.create_credit_offer(
            user_id=offer_data.user_id,
            offered_limit=offer_data.offered_limit,
            interest_rate=offer_data.interest_rate,
            model_version=offer_data.model_version,
            risk_assessment=offer_data.risk_assessment,
            emotional_context=offer_data.emotional_context,
            expires_in_hours=offer_data.expires_in_hours
        )
        
        # Schedule notification to user about new offer
        background_tasks.add_task(
            send_credit_notification.delay,
            user_id=offer.user_id,
            notification_type="offer_ready",
            title="New Credit Offer Available! 💳",
            message=f"You've been pre-approved for a credit limit of ${offer.offered_limit:,.2f}. Review and accept your offer before it expires.",
            metadata={"offer_id": offer.id}
        )
        
        logger.info(f"Created credit offer {offer.id} for user {offer.user_id}")
        
        return offer
        
    except Exception as e:
        logger.error(f"Failed to create credit offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credit offer: {str(e)}"
        )

@router.post("/offers/{offer_id}/accept", response_model=OfferAcceptanceResponse)
def accept_credit_offer(
    offer_id: int,
    acceptance_data: OfferAcceptanceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """
    Accept a credit offer and trigger asynchronous deployment
    
    This endpoint:
    1. Validates the offer is still available
    2. Records the acceptance
    3. Schedules background deployment task
    4. Returns immediately with tracking information
    """
    try:
        if not acceptance_data.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Terms and conditions must be accepted"
            )
        
        service = CreditDeploymentService(db)
        
        # Accept the offer
        result = service.accept_credit_offer(offer_id, acceptance_data.user_id)
        
        # Schedule asynchronous deployment
        background_tasks.add_task(
            deploy_credit_to_account.delay,
            offer_id=offer_id,
            task_id=result["task_id"]
        )
        
        logger.info(f"Credit offer {offer_id} accepted by user {acceptance_data.user_id}")
        
        return OfferAcceptanceResponse(
            offer_id=offer_id,
            task_id=result["task_id"],
            status=result["status"],
            deployment_scheduled=result["deployment_scheduled"],
            message=result["message"],
            estimated_completion="2-5 minutes"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to accept credit offer {offer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept credit offer: {str(e)}"
        )

@router.get("/offers/{offer_id}/status", response_model=DeploymentStatusResponse)
def get_deployment_status(
    offer_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """
    Get real-time status of credit offer deployment
    
    Provides detailed tracking information for the asynchronous deployment process.
    """
    try:
        service = CreditDeploymentService(db)
        
        # Get offer details
        offer = db.query(CreditOffer).filter(
            CreditOffer.id == offer_id,
            CreditOffer.user_id == user_id
        ).first()
        
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit offer not found"
            )
        
        # Get deployment history
        events = service.get_deployment_history(offer_id)
        
        # Determine current step and progress
        current_step, progress = _determine_deployment_progress(offer, events)
        
        event_data = [
            {
                "event_type": event.event_type,
                "success": event.success,
                "created_at": event.created_at.isoformat(),
                "processing_time_ms": event.processing_time_ms,
                "data": event.event_data
            }
            for event in events
        ]
        
        return DeploymentStatusResponse(
            offer_id=offer_id,
            status=offer.status,
            deployment_progress=progress,
            events=event_data,
            current_step=current_step,
            estimated_completion="2-5 minutes" if offer.status == "accepted" else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status for offer {offer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment status: {str(e)}"
        )

@router.get("/users/{user_id}/offers", response_model=List[CreditOfferResponse])
def get_user_credit_offers(
    user_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """Get all credit offers for a user, optionally filtered by status"""
    try:
        service = CreditDeploymentService(db)
        offers = service.get_user_credit_offers(user_id, status)
        
        return offers
        
    except Exception as e:
        logger.error(f"Failed to get credit offers for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credit offers: {str(e)}"
        )

@router.get("/users/{user_id}/summary", response_model=UserCreditSummary)
def get_user_credit_summary(
    user_id: int,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """Get comprehensive credit summary for a user"""
    try:
        from app.credit_models.credit_deployment import UserCreditProfile
        
        # Get credit profile
        profile = db.query(UserCreditProfile).filter(
            UserCreditProfile.user_id == user_id
        ).first()
        
        # Count pending offers
        pending_offers = db.query(CreditOffer).filter(
            CreditOffer.user_id == user_id,
            CreditOffer.status == CreditOfferStatus.PENDING
        ).count()
        
        if not profile:
            # Return default profile if none exists
            return UserCreditSummary(
                user_id=user_id,
                current_limit=0.0,
                available_credit=0.0,
                used_credit=0.0,
                interest_rate=None,
                pending_offers=pending_offers,
                last_limit_increase=None,
                emotional_stability_score=None
            )
        
        return UserCreditSummary(
            user_id=user_id,
            current_limit=profile.current_limit,
            available_credit=profile.available_credit,
            used_credit=profile.used_credit,
            interest_rate=profile.current_interest_rate,
            pending_offers=pending_offers,
            last_limit_increase=profile.last_limit_increase,
            emotional_stability_score=profile.emotional_stability_score
        )
        
    except Exception as e:
        logger.error(f"Failed to get credit summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credit summary: {str(e)}"
        )

@router.post("/notifications/send")
def send_test_notification(
    user_id: int,
    title: str,
    message: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: bool = Depends(basic_auth)
):
    """Send a test notification (for development/testing)"""
    try:
        background_tasks.add_task(
            send_credit_notification.delay,
            user_id=user_id,
            notification_type="test",
            title=title,
            message=message,
            metadata={"test": True}
        )
        
        return {"status": "scheduled", "user_id": user_id, "message": "Notification scheduled"}
        
    except Exception as e:
        logger.error(f"Failed to schedule test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )

def _determine_deployment_progress(offer: CreditOffer, events: List[CreditDeploymentEvent]) -> tuple[str, str]:
    """Determine current deployment step and progress percentage"""
    
    if offer.status == CreditOfferStatus.PENDING:
        return "Awaiting user acceptance", "0%"
    elif offer.status == CreditOfferStatus.ACCEPTED:
        if any(e.event_type == "credit_deployed" for e in events):
            return "Deployment completed", "100%"
        elif any(e.event_type == "deployment_started" for e in events):
            return "Updating account", "75%"
        else:
            return "Processing deployment", "25%"
    elif offer.status == CreditOfferStatus.DEPLOYED:
        return "Deployment completed", "100%"
    elif offer.status == CreditOfferStatus.FAILED:
        return "Deployment failed", "Error"
    elif offer.status == CreditOfferStatus.EXPIRED:
        return "Offer expired", "N/A"
    else:
        return "Unknown status", "N/A"
