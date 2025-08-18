"""
CloudWalk ECS App - Privacy and Analytics API Endpoints
=======================================================

This module provides REST API endpoints for data privacy management and emotional analytics.
Includes GDPR compliance endpoints, consent management, and comprehensive analytics APIs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets
import logging

from app.core.db import get_db
from app.privacy.data_privacy_manager import privacy_manager, ConsentProfile, DataRetentionLevel, ConsentType
from app.analytics.emotion_analytics import analytics_engine, EmotionTrend, RiskLevel
from pydantic import BaseModel, Field


# ==================== AUTHENTICATION ====================

security = HTTPBasic()
logger = logging.getLogger(__name__)

def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials for privacy and analytics endpoints"""
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "test")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ==================== PYDANTIC MODELS ====================

class ConsentUpdateRequest(BaseModel):
    """Request model for updating user consent"""
    basic_emotions: bool = True
    detailed_emotions: bool = False
    biometric_data: bool = False
    location_context: bool = False
    research_analytics: bool = False
    marketing_insights: bool = False
    retention_level: DataRetentionLevel = DataRetentionLevel.STANDARD


class UserDataExportResponse(BaseModel):
    """Response model for user data export"""
    user_id: int
    export_data: Dict[str, Any]
    export_timestamp: datetime
    gdpr_compliant: bool = True


class PrivacyMetricsResponse(BaseModel):
    """Response model for privacy metrics"""
    total_users: int
    consented_users: int
    anonymized_records: int
    deleted_records: int
    encryption_coverage: float
    gdpr_requests_processed: int
    privacy_violations: int
    compliance_score: float


class EmotionalProfileResponse(BaseModel):
    """Response model for user emotional profile"""
    user_id: int
    dominant_emotions: List[str]
    emotional_stability: float
    stress_level: float
    recent_trend: EmotionTrend
    risk_level: RiskLevel
    total_events: int
    analysis_period_days: int
    last_updated: datetime


class SystemTrendsResponse(BaseModel):
    """Response model for system emotional trends"""
    time_period: str
    total_events: int
    unique_users: int
    top_emotions: List[Dict]
    emotional_volatility: float
    stress_indicators: Dict[str, float]
    anomaly_alerts: List[Dict]


class LiveMetricsResponse(BaseModel):
    """Response model for live emotion metrics"""
    current_active_users: int
    emotions_per_minute: float
    dominant_emotion_now: str
    valence_distribution: Dict[str, float]
    arousal_distribution: Dict[str, float]
    stress_level_alert: bool
    anomaly_detected: bool
    last_updated: datetime


# ==================== ROUTER SETUP ====================

router = APIRouter(prefix="/api/v1", tags=["Privacy & Analytics"])


# ==================== PRIVACY ENDPOINTS ====================

@router.post("/privacy/consent/{user_id}", response_model=Dict[str, str])
async def update_user_consent(
    user_id: int = Path(..., description="User ID"),
    consent_request: ConsentUpdateRequest = ...,
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Update user consent preferences for data processing.
    
    This endpoint allows updating user consent for various types of data processing
    including emotional analysis, biometric data, and research analytics.
    """
    try:
        consent_profile = ConsentProfile(
            user_id=user_id,
            basic_emotions=consent_request.basic_emotions,
            detailed_emotions=consent_request.detailed_emotions,
            biometric_data=consent_request.biometric_data,
            location_context=consent_request.location_context,
            research_analytics=consent_request.research_analytics,
            marketing_insights=consent_request.marketing_insights,
            retention_level=consent_request.retention_level,
            consent_date=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        success = await privacy_manager.update_user_consent(user_id, consent_profile)
        
        if success:
            logger.info(f"Consent updated for user {user_id} by admin")
            return {
                "status": "success",
                "message": f"Consent updated for user {user_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user consent"
            )
    
    except Exception as e:
        logger.error(f"Failed to update consent for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/privacy/consent/{user_id}", response_model=Dict[str, Any])
async def get_user_consent(
    user_id: int = Path(..., description="User ID"),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get current consent preferences for a user.
    """
    try:
        consent_profile = await privacy_manager.get_user_consent(user_id)
        
        if consent_profile:
            return {
                "user_id": consent_profile.user_id,
                "basic_emotions": consent_profile.basic_emotions,
                "detailed_emotions": consent_profile.detailed_emotions,
                "biometric_data": consent_profile.biometric_data,
                "location_context": consent_profile.location_context,
                "research_analytics": consent_profile.research_analytics,
                "marketing_insights": consent_profile.marketing_insights,
                "retention_level": consent_profile.retention_level.value,
                "consent_date": consent_profile.consent_date.isoformat() if consent_profile.consent_date else None,
                "last_updated": consent_profile.last_updated.isoformat() if consent_profile.last_updated else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consent profile not found for user {user_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consent for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/privacy/user-data/{user_id}", response_model=Dict[str, str])
async def delete_user_data(
    user_id: int = Path(..., description="User ID"),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Handle GDPR right to erasure request - delete all user data.
    
    This endpoint permanently deletes all emotional data for a user
    in compliance with GDPR Article 17 (Right to Erasure).
    """
    try:
        success = await privacy_manager.handle_right_to_erasure(user_id)
        
        if success:
            logger.info(f"GDPR erasure request processed for user {user_id} by admin")
            return {
                "status": "success",
                "message": f"All data for user {user_id} has been permanently deleted",
                "timestamp": datetime.utcnow().isoformat(),
                "gdpr_compliant": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process data deletion request"
            )
    
    except Exception as e:
        logger.error(f"Failed to delete data for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/privacy/export/{user_id}", response_model=UserDataExportResponse)
async def export_user_data(
    user_id: int = Path(..., description="User ID"),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Export all user data for GDPR data portability compliance.
    
    This endpoint exports all user data in a structured format
    in compliance with GDPR Article 20 (Right to Data Portability).
    """
    try:
        export_data = await privacy_manager.export_user_data(user_id)
        
        if export_data:
            return UserDataExportResponse(
                user_id=user_id,
                export_data=export_data,
                export_timestamp=datetime.utcnow(),
                gdpr_compliant=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for user {user_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export data for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/privacy/enforce-retention", response_model=Dict[str, str])
async def enforce_data_retention(
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Manually trigger data retention policy enforcement.
    
    This endpoint manually triggers the enforcement of data retention policies,
    anonymizing or deleting data based on user consent and retention settings.
    """
    try:
        await privacy_manager.enforce_data_retention()
        
        logger.info("Data retention policies enforced by admin")
        return {
            "status": "success",
            "message": "Data retention policies enforced successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to enforce data retention: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/privacy/metrics", response_model=PrivacyMetricsResponse)
async def get_privacy_metrics(
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get privacy compliance metrics and statistics.
    """
    try:
        metrics = await privacy_manager.get_privacy_metrics()
        
        # Calculate compliance score
        compliance_score = min(100.0, (
            metrics.encryption_coverage * 0.3 +
            (metrics.consented_users / max(1, metrics.total_users)) * 100 * 0.3 +
            (100 - metrics.privacy_violations) * 0.4
        ))
        
        return PrivacyMetricsResponse(
            total_users=metrics.total_users,
            consented_users=metrics.consented_users,
            anonymized_records=metrics.anonymized_records,
            deleted_records=metrics.deleted_records,
            encryption_coverage=metrics.encryption_coverage,
            gdpr_requests_processed=metrics.gdpr_requests_processed,
            privacy_violations=metrics.privacy_violations,
            compliance_score=compliance_score
        )
    
    except Exception as e:
        logger.error(f"Failed to get privacy metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/user/{user_id}/profile", response_model=EmotionalProfileResponse)
async def get_user_emotional_profile(
    user_id: int = Path(..., description="User ID"),
    days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get comprehensive emotional profile for a specific user.
    
    This endpoint provides detailed emotional analysis including dominant emotions,
    stability metrics, stress levels, and risk assessment for credit decisions.
    """
    try:
        profile = await analytics_engine.analyze_user_emotional_profile(user_id, days)
        
        return EmotionalProfileResponse(
            user_id=profile.user_id,
            dominant_emotions=profile.dominant_emotions,
            emotional_stability=profile.emotional_stability,
            stress_level=profile.stress_level,
            recent_trend=profile.recent_trend,
            risk_level=profile.risk_level,
            total_events=profile.total_events,
            analysis_period_days=profile.analysis_period_days,
            last_updated=profile.last_updated
        )
    
    except Exception as e:
        logger.error(f"Failed to get emotional profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analytics/system/trends", response_model=SystemTrendsResponse)
async def get_system_emotional_trends(
    hours: int = Query(24, description="Analysis period in hours", ge=1, le=168),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get system-wide emotional trends and insights.
    
    This endpoint provides comprehensive system-level emotional analysis including
    top emotions, trend data, stress indicators, and anomaly detection.
    """
    try:
        trends = await analytics_engine.analyze_system_emotional_trends(hours)
        
        # Convert emotion insights to dictionaries
        top_emotions_dict = []
        for emotion in trends.top_emotions:
            top_emotions_dict.append({
                "emotion_label": emotion.emotion_label,
                "frequency": emotion.frequency,
                "percentage": emotion.percentage,
                "avg_valence": emotion.avg_valence,
                "avg_arousal": emotion.avg_arousal,
                "trend": emotion.trend.value,
                "confidence": emotion.confidence
            })
        
        return SystemTrendsResponse(
            time_period=trends.time_period,
            total_events=trends.total_events,
            unique_users=trends.unique_users,
            top_emotions=top_emotions_dict,
            emotional_volatility=trends.emotional_volatility,
            stress_indicators=trends.stress_indicators,
            anomaly_alerts=trends.anomaly_alerts
        )
    
    except Exception as e:
        logger.error(f"Failed to get system trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analytics/live/metrics", response_model=LiveMetricsResponse)
async def get_live_emotion_metrics(
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get real-time emotion metrics for live dashboard display.
    
    This endpoint provides real-time emotional metrics including active users,
    current dominant emotion, valence/arousal distributions, and alerts.
    """
    try:
        metrics = await analytics_engine.get_live_emotion_metrics()
        
        return LiveMetricsResponse(
            current_active_users=metrics.current_active_users,
            emotions_per_minute=metrics.emotions_per_minute,
            dominant_emotion_now=metrics.dominant_emotion_now,
            valence_distribution=metrics.valence_distribution,
            arousal_distribution=metrics.arousal_distribution,
            stress_level_alert=metrics.stress_level_alert,
            anomaly_detected=metrics.anomaly_detected,
            last_updated=metrics.last_updated
        )
    
    except Exception as e:
        logger.error(f"Failed to get live metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analytics/credit/correlations", response_model=List[Dict[str, Any]])
async def get_credit_emotion_correlations(
    days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Get correlation analysis between emotional states and credit decisions.
    
    This endpoint provides insights into how different emotional states
    correlate with credit approval rates, amounts, and default risks.
    """
    try:
        correlations = await analytics_engine.analyze_credit_emotion_correlation(days)
        
        correlation_data = []
        for corr in correlations:
            correlation_data.append({
                "emotion_label": corr.emotion_label,
                "approval_rate": corr.approval_rate,
                "avg_credit_amount": corr.avg_credit_amount,
                "default_risk_correlation": corr.default_risk_correlation,
                "sample_size": corr.sample_size
            })
        
        return correlation_data
    
    except Exception as e:
        logger.error(f"Failed to get credit correlations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/analytics/export", response_model=Dict[str, Any])
async def export_emotion_insights(
    format: str = Query("json", description="Export format", regex="^(json|csv)$"),
    credentials: str = Depends(verify_admin_credentials)
):
    """
    Export comprehensive emotional insights and analytics data.
    
    This endpoint exports all available emotional analytics data including
    trends, correlations, and live metrics in the specified format.
    """
    try:
        insights = await analytics_engine.export_emotion_insights(format)
        
        return {
            "export_format": format,
            "export_timestamp": datetime.utcnow().isoformat(),
            "data": insights
        }
    
    except Exception as e:
        logger.error(f"Failed to export emotion insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/dashboard/emotion-overview", response_model=Dict[str, Any])
async def get_dashboard_emotion_overview():
    """
    Get emotion overview data for the main dashboard (public endpoint).
    
    This endpoint provides basic emotional metrics for display on the main dashboard
    without requiring authentication for real-time visualization.
    """
    try:
        # Get basic live metrics (public data only)
        live_metrics = await analytics_engine.get_live_emotion_metrics()
        trends_24h = await analytics_engine.analyze_system_emotional_trends(24)
        
        # Return only non-sensitive aggregated data
        return {
            "current_active_users": live_metrics.current_active_users,
            "dominant_emotion": live_metrics.dominant_emotion_now,
            "total_events_24h": trends_24h.total_events,
            "emotional_volatility": trends_24h.emotional_volatility,
            "stress_level": trends_24h.stress_indicators.get("overall_stress_level", 0.0),
            "valence_distribution": live_metrics.valence_distribution,
            "last_updated": live_metrics.last_updated.isoformat(),
            "privacy_note": "This data is aggregated and anonymized for public display"
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        # Return default safe data on error
        return {
            "current_active_users": 0,
            "dominant_emotion": "neutral",
            "total_events_24h": 0,
            "emotional_volatility": 0.0,
            "stress_level": 0.0,
            "valence_distribution": {"neutral": 100},
            "last_updated": datetime.utcnow().isoformat(),
            "error": "Data temporarily unavailable"
        }
