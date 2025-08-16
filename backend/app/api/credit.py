from fastapi import APIRouter, HTTPException, Depends
from app.auth import basic_auth
from app.tasks.credit import evaluate_credit
from app.services.credit_service import calculate_credit_offer
from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Response models for API documentation
class MLModelResult(BaseModel):
    """ML model specific results"""
    risk_score: float
    approval_decision: bool
    model_version: str
    features_processed: Dict[str, Any]
    approval_threshold: float

class CreditOfferDetails(BaseModel):
    """Credit offer details when approved"""
    credit_limit: float
    interest_rate: float
    credit_type: str

class CreditLimitAPIResponse(BaseModel):
    """
    Complete response model matching the exact requirements:
    1) ML model result and approval decision
    2) Credit limit and interest rate 
    3) Credit type (Short-Term, Long-Term)
    """
    user_id: int
    ml_model_result: MLModelResult
    approved: bool
    credit_offer: Optional[CreditOfferDetails] = None
    message: str

class AsyncCreditResponse(BaseModel):
    """Response model for async credit evaluation"""
    task_id: str
    status: str

router = APIRouter(prefix="/credit", tags=["credit"])

@router.post("/calculate/{user_id}", response_model=CreditLimitAPIResponse)
def calculate_credit_limit(user_id: int, auth: bool = Depends(basic_auth)):
    """
    RESTful API endpoint that calculates and returns:
    1) The ML model result and approval decision
    2) The credit limit and interest rate (if approved)
    3) Credit type (Short-Term, Long-Term)
    
    Accepts: user_id as path parameter
    Returns: Complete credit evaluation with ML model results
    """
    try:
        # Call the credit service with integrated ML model
        credit_result = calculate_credit_offer(user_id)
        
        # 1) ML Model Result
        ml_model_result = MLModelResult(
            risk_score=credit_result["risk_score"],
            approval_decision=credit_result["approved"],
            model_version="v1.0.0",
            features_processed=credit_result["features_used"],
            approval_threshold=0.6
        )
        
        # 2) Credit Limit and Interest Rate + 3) Credit Type
        credit_offer = None
        if credit_result["approved"]:
            credit_offer = CreditOfferDetails(
                credit_limit=credit_result["new_credit_limit"],
                interest_rate=credit_result["interest_rate"],
                credit_type=credit_result["credit_type"]
            )
        
        # Generate appropriate message
        if credit_result["approved"]:
            message = f"Credit approved! Risk score: {credit_result['risk_score']:.3f}"
        else:
            message = f"Credit denied. Risk score: {credit_result['risk_score']:.3f} (threshold: 0.6)"
        
        response = CreditLimitAPIResponse(
            user_id=user_id,
            ml_model_result=ml_model_result,
            approved=credit_result["approved"],
            credit_offer=credit_offer,
            message=message
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credit calculation failed: {str(e)}")

@router.get("/calculate/{user_id}", response_model=CreditLimitAPIResponse)
def get_credit_limit(user_id: int, auth: bool = Depends(basic_auth)):
    """
    Alternative GET endpoint for credit limit calculation.
    Same functionality as POST but follows REST conventions for read operations.
    """
    return calculate_credit_limit(user_id)

@router.post("/evaluate/{user_id}", response_model=AsyncCreditResponse)
def evaluate_credit_endpoint(user_id: int, auth: bool = Depends(basic_auth)):
    """
    Trigger asynchronous credit evaluation for a given user.
    Returns Celery task ID for long-running operations.
    """
    task = evaluate_credit.delay(user_id)
    return AsyncCreditResponse(task_id=task.id, status="pending")

status_router = APIRouter(prefix="/credit/status", tags=["credit"])

@status_router.get("/{task_id}")
def credit_status(task_id: str, auth: bool = Depends(basic_auth)):
    """Get the status of an asynchronous credit evaluation task"""
    task_result = AsyncResult(task_id)
    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif task_result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task_result.info)}
    else:
        return {"task_id": task_id, "status": task_result.state.lower(), "result": task_result.result}

# Additional utility endpoints
@router.get("/demo/{user_id}")
def credit_limit_demo(user_id: int, auth: bool = Depends(basic_auth)):
    """
    Demo endpoint showing the complete credit limit calculation process.
    Perfect for testing and demonstrating the API requirements.
    """
    try:
        # Get the full credit calculation
        credit_result = calculate_credit_offer(user_id)
        
        return {
            "demo_title": "CloudWalk Empathic Credit System - Credit Limit API Demo",
            "user_id": user_id,
            
            # Requirement 1: ML Model Result
            "1_ml_model_result": {
                "risk_score": credit_result["risk_score"],
                "approval_decision": credit_result["approved"],
                "model_features_used": credit_result["features_used"],
                "approval_threshold": 0.6,
                "risk_explanation": "0.0 = lowest risk, 1.0 = highest risk"
            },
            
            # Requirement 2: Credit Limit and Interest Rate
            "2_financial_terms": {
                "credit_limit": credit_result["new_credit_limit"] if credit_result["approved"] else 0,
                "interest_rate": credit_result["interest_rate"],
                "interest_rate_explanation": f"Base rate (15%) + Risk premium ({credit_result['risk_score'] * 10:.1f}%)"
            },
            
            # Requirement 3: Credit Type
            "3_credit_type": {
                "type": credit_result["credit_type"],
                "type_explanation": {
                    "Long-Term": "Low risk customers with emotional stability",
                    "Short-Term": "Medium-high risk or emotionally volatile customers", 
                    "Rejected": "High risk customers (score >= 0.6)"
                }
            },
            
            "summary": {
                "status": "APPROVED" if credit_result["approved"] else "DENIED",
                "recommendation": "Proceed with credit offer" if credit_result["approved"] else "Review application manually"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.get("/model/info")
def get_ml_model_info(auth: bool = Depends(basic_auth)):
    """Get information about the ML model being used"""
    from app.ml.model import get_credit_risk_model
    
    model = get_credit_risk_model()
    model_info = model.get_model_info()
    
    return {
        "model_info": model_info,
        "endpoint_info": {
            "approval_threshold": 0.6,
            "risk_scale": "0.0 (low risk) to 1.0 (high risk)",
            "features_required": list(model_info["features"])
        }
    }

@router.get("/limits/{user_id}")
def get_current_credit_limits(user_id: int, auth: bool = Depends(basic_auth)):
    """Get current credit information for a user without running ML evaluation"""
    try:
        from app.core.db import SessionLocal
        
        # Import User model to avoid any conflicts
        from app.models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "user_id": user_id,
                "current_credit_limit": user.credit_limit,
                "credit_type": user.credit_type,
                "last_updated": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None
            }
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credit limits: {str(e)}")
