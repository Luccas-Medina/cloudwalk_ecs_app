# app/api/monitoring.py
"""
Circuit Breaker and Service Health Monitoring API

This module provides endpoints for monitoring the health and status
of circuit breakers and protected services in the application.

Features:
- Circuit breaker status monitoring
- Service health checks
- Performance metrics
- Manual circuit breaker control
- Comprehensive system diagnostics
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from app.auth import basic_auth
from app.patterns.circuit_breaker import (
    get_all_circuit_breakers,
    get_circuit_breaker_status,
    get_circuit_breaker
)
from app.ml.protected_model import get_protected_ml_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", summary="Overall system health check")
def get_system_health(auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get comprehensive system health information
    
    Returns:
        Dictionary containing overall system health status
    """
    try:
        ml_service = get_protected_ml_service()
        ml_health = ml_service.get_service_health()
        
        circuit_breakers = get_circuit_breaker_status()
        
        # Calculate overall system health
        overall_health = _calculate_overall_health(ml_health, circuit_breakers)
        
        return {
            "timestamp": "2025-08-16T20:00:00Z",
            "overall_status": overall_health["status"],
            "overall_score": overall_health["score"],
            "services": {
                "ml_model_service": ml_health
            },
            "circuit_breakers": circuit_breakers,
            "recommendations": overall_health["recommendations"]
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/circuit-breakers", summary="Get all circuit breaker statuses")
def get_circuit_breakers_status(auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get status of all registered circuit breakers
    
    Returns:
        Dictionary containing status of all circuit breakers
    """
    try:
        return {
            "timestamp": "2025-08-16T20:00:00Z",
            "circuit_breakers": get_circuit_breaker_status()
        }
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get circuit breaker status: {str(e)}")


@router.get("/circuit-breakers/{breaker_name}", summary="Get specific circuit breaker status")
def get_circuit_breaker_details(breaker_name: str, auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get detailed status of a specific circuit breaker
    
    Args:
        breaker_name: Name of the circuit breaker
        
    Returns:
        Detailed circuit breaker status and metrics
    """
    try:
        breaker = get_circuit_breaker(breaker_name)
        if not breaker:
            raise HTTPException(status_code=404, detail=f"Circuit breaker '{breaker_name}' not found")
        
        return {
            "timestamp": "2025-08-16T20:00:00Z",
            "circuit_breaker": breaker.get_status()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breaker details for {breaker_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get circuit breaker details: {str(e)}")


@router.post("/circuit-breakers/{breaker_name}/reset", summary="Reset circuit breaker")
def reset_circuit_breaker(breaker_name: str, auth: bool = Depends(basic_auth)) -> Dict[str, str]:
    """
    Manually reset a circuit breaker to closed state
    
    Args:
        breaker_name: Name of the circuit breaker to reset
        
    Returns:
        Success confirmation
    """
    try:
        if breaker_name == "ml_model_service":
            ml_service = get_protected_ml_service()
            ml_service.reset_circuit_breaker()
        else:
            breaker = get_circuit_breaker(breaker_name)
            if not breaker:
                raise HTTPException(status_code=404, detail=f"Circuit breaker '{breaker_name}' not found")
            breaker.reset()
        
        logger.info(f"Circuit breaker '{breaker_name}' manually reset")
        return {
            "message": f"Circuit breaker '{breaker_name}' has been reset to closed state",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker {breaker_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {str(e)}")


@router.post("/circuit-breakers/{breaker_name}/open", summary="Force circuit breaker open")
def force_circuit_breaker_open(breaker_name: str, auth: bool = Depends(basic_auth)) -> Dict[str, str]:
    """
    Manually force a circuit breaker to open state
    
    Args:
        breaker_name: Name of the circuit breaker to open
        
    Returns:
        Success confirmation
    """
    try:
        if breaker_name == "ml_model_service":
            ml_service = get_protected_ml_service()
            ml_service.force_circuit_open()
        else:
            breaker = get_circuit_breaker(breaker_name)
            if not breaker:
                raise HTTPException(status_code=404, detail=f"Circuit breaker '{breaker_name}' not found")
            breaker.force_open()
        
        logger.warning(f"Circuit breaker '{breaker_name}' manually forced open")
        return {
            "message": f"Circuit breaker '{breaker_name}' has been forced to open state",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing circuit breaker {breaker_name} open: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to force circuit breaker open: {str(e)}")


@router.get("/ml-service/health", summary="ML service health details")
def get_ml_service_health(auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get detailed health information for the ML model service
    
    Returns:
        Comprehensive ML service health data
    """
    try:
        ml_service = get_protected_ml_service()
        health_data = ml_service.get_service_health()
        
        return {
            "timestamp": "2025-08-16T20:00:00Z",
            "ml_service_health": health_data
        }
        
    except Exception as e:
        logger.error(f"Error getting ML service health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ML service health: {str(e)}")


@router.get("/ml-service/metrics", summary="ML service performance metrics")
def get_ml_service_metrics(auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get performance metrics for the ML model service
    
    Returns:
        ML service performance metrics and statistics
    """
    try:
        ml_service = get_protected_ml_service()
        health_data = ml_service.get_service_health()
        
        # Extract and format metrics
        metrics = health_data['performance_metrics']
        circuit_metrics = health_data['circuit_breaker']['metrics']
        
        return {
            "timestamp": "2025-08-16T20:00:00Z",
            "performance_metrics": {
                "total_predictions": metrics['total_predictions'],
                "model_predictions": metrics['model_predictions'],
                "fallback_predictions": metrics['fallback_predictions'],
                "fallback_rate": (metrics['fallback_predictions'] / metrics['total_predictions'] 
                                if metrics['total_predictions'] > 0 else 0),
                "average_response_time": metrics['average_response_time'],
                "last_prediction_time": metrics['last_prediction_time']
            },
            "circuit_breaker_metrics": {
                "total_requests": circuit_metrics['total_requests'],
                "success_rate": (circuit_metrics['successful_requests'] / circuit_metrics['total_requests'] 
                               if circuit_metrics['total_requests'] > 0 else 0),
                "failure_rate": circuit_metrics['failure_rate'],
                "recent_failure_rate": circuit_metrics['recent_failure_rate'],
                "circuit_open_count": circuit_metrics['circuit_open_count'],
                "average_response_time": circuit_metrics['average_response_time']
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting ML service metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ML service metrics: {str(e)}")


@router.get("/diagnostics", summary="Comprehensive system diagnostics")
def get_system_diagnostics(auth: bool = Depends(basic_auth)) -> Dict[str, Any]:
    """
    Get comprehensive system diagnostics and troubleshooting information
    
    Returns:
        Detailed system diagnostics for troubleshooting
    """
    try:
        ml_service = get_protected_ml_service()
        ml_health = ml_service.get_service_health()
        circuit_breakers = get_circuit_breaker_status()
        
        # Generate diagnostics
        diagnostics = {
            "timestamp": "2025-08-16T20:00:00Z",
            "system_status": _calculate_overall_health(ml_health, circuit_breakers),
            "service_details": {
                "ml_model_service": ml_health
            },
            "circuit_breaker_details": circuit_breakers,
            "potential_issues": _identify_potential_issues(ml_health, circuit_breakers),
            "recommended_actions": _get_recommended_actions(ml_health, circuit_breakers)
        }
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error getting system diagnostics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system diagnostics: {str(e)}")


def _calculate_overall_health(ml_health: Dict[str, Any], circuit_breakers: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall system health score and status"""
    
    # Weight ML service health heavily since it's critical
    ml_weight = 0.8
    circuit_weight = 0.2
    
    ml_score = ml_health['health_score']
    
    # Calculate average circuit breaker health
    if circuit_breakers:
        circuit_scores = []
        for breaker_name, breaker_status in circuit_breakers.items():
            # Convert circuit breaker state to health score
            state = breaker_status['state']
            if state == 'closed':
                circuit_scores.append(100)
            elif state == 'half_open':
                circuit_scores.append(60)
            else:  # open
                circuit_scores.append(20)
        
        avg_circuit_score = sum(circuit_scores) / len(circuit_scores)
    else:
        avg_circuit_score = 100  # No circuit breakers means no issues
    
    # Calculate weighted overall score
    overall_score = (ml_score * ml_weight) + (avg_circuit_score * circuit_weight)
    
    # Determine status
    if overall_score >= 90:
        status = "healthy"
    elif overall_score >= 75:
        status = "degraded"
    elif overall_score >= 50:
        status = "unhealthy"
    else:
        status = "critical"
    
    # Generate recommendations
    recommendations = []
    if ml_score < 80:
        recommendations.extend(ml_health['recommendations'])
    
    if avg_circuit_score < 80:
        recommendations.append("Circuit breaker issues detected - check service stability")
    
    if not recommendations:
        recommendations.append("System is operating normally")
    
    return {
        "score": round(overall_score, 1),
        "status": status,
        "recommendations": recommendations
    }


def _identify_potential_issues(ml_health: Dict[str, Any], circuit_breakers: Dict[str, Any]) -> List[str]:
    """Identify potential system issues based on health data"""
    issues = []
    
    # ML service issues
    if ml_health['health_score'] < 70:
        issues.append(f"ML service health is {ml_health['status']} (score: {ml_health['health_score']})")
    
    # Circuit breaker issues
    for breaker_name, breaker_status in circuit_breakers.items():
        if breaker_status['state'] == 'open':
            issues.append(f"Circuit breaker '{breaker_name}' is open")
        elif breaker_status['state'] == 'half_open':
            issues.append(f"Circuit breaker '{breaker_name}' is in recovery mode")
        
        failure_rate = breaker_status['metrics']['recent_failure_rate']
        if failure_rate > 0.2:
            issues.append(f"High failure rate ({failure_rate:.1%}) for '{breaker_name}'")
    
    return issues


def _get_recommended_actions(ml_health: Dict[str, Any], circuit_breakers: Dict[str, Any]) -> List[str]:
    """Get recommended actions based on system health"""
    actions = []
    
    # ML service recommendations
    if ml_health['health_score'] < 80:
        actions.extend(ml_health['recommendations'])
    
    # Circuit breaker recommendations
    for breaker_name, breaker_status in circuit_breakers.items():
        if breaker_status['state'] == 'open':
            actions.append(f"Investigate and fix issues causing '{breaker_name}' to be open")
        
        failure_rate = breaker_status['metrics']['recent_failure_rate']
        if failure_rate > 0.3:
            actions.append(f"Address high failure rate for '{breaker_name}' service")
    
    # General recommendations
    if any(cb['state'] != 'closed' for cb in circuit_breakers.values()):
        actions.append("Monitor service logs for error patterns")
        actions.append("Consider scaling or optimizing affected services")
    
    if not actions:
        actions.append("Continue monitoring - system is healthy")
    
    return actions
