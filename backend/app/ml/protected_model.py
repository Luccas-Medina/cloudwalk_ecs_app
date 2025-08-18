# app/ml/protected_model.py
"""
Circuit Breaker Protected ML Model Service

This module wraps the ML model with circuit breaker protection to handle
failures gracefully and provide fallback mechanisms for credit scoring.

Features:
- Circuit breaker protection for ML model calls
- Intelligent fallback scoring algorithms
- Comprehensive error handling and recovery
- Performance monitoring and alerting
- Graceful degradation under load
"""

import logging
import random
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.patterns.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitBreakerError,
    CircuitBreakerTimeoutError,
    register_circuit_breaker
)
from app.ml.model import CreditRiskModel

logger = logging.getLogger(__name__)


class MLModelServiceError(Exception):
    """Exception for ML model service errors"""
    pass


class ProtectedMLModelService:
    """
    ML Model service with circuit breaker protection
    
    This class provides a resilient interface to the ML model with:
    - Automatic failure detection and recovery
    - Fallback scoring when ML service is unavailable
    - Performance monitoring and metrics
    - Configurable circuit breaker behavior
    """
    
    def __init__(self):
        """Initialize the protected ML model service"""
        
        # Initialize the underlying ML model
        self.ml_model = CreditRiskModel()
        
        # Configure circuit breaker for ML model protection
        self.circuit_config = CircuitBreakerConfig(
            failure_threshold=3,          # Open after 3 consecutive failures
            recovery_timeout=30.0,        # Wait 30 seconds before testing recovery
            success_threshold=2,          # Need 2 successes to close circuit
            timeout=5.0,                  # 5 second timeout for ML calls
            expected_exception=(MLModelServiceError, TimeoutError, ConnectionError),
            fallback_enabled=True,
            metrics_window_size=50
        )
        
        # Create circuit breaker with fallback
        self.circuit_breaker = CircuitBreaker(
            name="ml_model_service",
            config=self.circuit_config,
            fallback_func=self._fallback_risk_score
        )
        
        # Register circuit breaker for monitoring
        register_circuit_breaker(self.circuit_breaker)
        
        # Performance tracking
        self.performance_metrics = {
            'total_predictions': 0,
            'fallback_predictions': 0,
            'model_predictions': 0,
            'average_response_time': 0.0,
            'last_prediction_time': None
        }
        
        logger.info("Protected ML Model Service initialized with circuit breaker protection")
    
    def predict_risk_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict credit risk score with circuit breaker protection
        
        Args:
            features: Dictionary of financial and emotional features
            
        Returns:
            Dictionary containing risk score and metadata
            
        The method will:
        1. Try to call the ML model through circuit breaker
        2. Fall back to rule-based scoring if ML service fails
        3. Track performance metrics and service health
        """
        start_time = time.time()
        self.performance_metrics['total_predictions'] += 1
        
        try:
            # Call ML model through circuit breaker protection
            result = self.circuit_breaker.call(self._call_ml_model, features)
            
            # Track successful ML model prediction
            self.performance_metrics['model_predictions'] += 1
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time)
            
            logger.info(f"ML model prediction successful in {response_time:.3f}s")
            
            return {
                'risk_score': result,
                'model_version': self.ml_model.model_version,
                'prediction_source': 'ml_model',
                'circuit_breaker_state': self.circuit_breaker.state.value,
                'response_time': response_time,
                'features_used': list(features.keys())
            }
            
        except CircuitBreakerError:
            # Circuit is open, use fallback directly
            logger.warning("Circuit breaker is open, using fallback scoring")
            return self._get_fallback_prediction(features, start_time)
            
        except Exception as e:
            # Unexpected error, log and use fallback
            logger.error(f"Unexpected error in ML model service: {e}")
            return self._get_fallback_prediction(features, start_time)
    
    def _call_ml_model(self, features: Dict[str, Any]) -> float:
        """
        Internal method to call the actual ML model
        
        This method simulates potential failures and timeouts
        that might occur in a real ML service deployment.
        """
        # Simulate occasional service failures for testing
        if random.random() < 0.1:  # 10% simulated failure rate
            failure_type = random.choice(['timeout', 'service_error', 'connection_error'])
            
            if failure_type == 'timeout':
                time.sleep(6)  # Simulate timeout (longer than circuit breaker timeout)
                raise TimeoutError("ML model service timeout")
            elif failure_type == 'service_error':
                raise MLModelServiceError("ML model service temporarily unavailable")
            else:
                raise ConnectionError("Unable to connect to ML model service")
        
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Call the actual ML model
        try:
            return self.ml_model.predict_risk_score(features)
        except Exception as e:
            raise MLModelServiceError(f"ML model prediction failed: {e}")
    
    def _fallback_risk_score(self, features: Dict[str, Any]) -> float:
        """
        Fallback risk scoring algorithm when ML model is unavailable
        
        This implements a rule-based credit risk assessment that provides
        reasonable risk scores based on traditional credit factors.
        
        Args:
            features: Financial and emotional features
            
        Returns:
            Risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        logger.info("Using fallback risk scoring algorithm")
        
        risk_score = 0.0
        
        # Financial risk factors
        transaction_count = features.get('transaction_count', 0)
        avg_transaction = features.get('avg_transaction_amount', 0)
        current_limit = features.get('current_credit_limit', 0)
        
        # Transaction volume risk
        if transaction_count == 0:
            risk_score += 0.3  # No transaction history is risky
        elif transaction_count < 5:
            risk_score += 0.2  # Low transaction history
        elif transaction_count > 100:
            risk_score -= 0.1  # High transaction volume is good
        
        # Transaction amount patterns
        if avg_transaction > current_limit * 0.8:
            risk_score += 0.2  # High utilization is risky
        elif avg_transaction < current_limit * 0.3:
            risk_score -= 0.1  # Conservative usage is good
        
        # Credit limit assessment
        if current_limit > 100000:
            risk_score -= 0.1  # High existing limit indicates trust
        elif current_limit < 10000:
            risk_score += 0.1  # Low limit may indicate higher risk
        
        # Emotional risk factors (if available)
        avg_valence = features.get('avg_valence')
        avg_arousal = features.get('avg_arousal')
        last_emotion = features.get('last_emotion')
        
        if avg_valence is not None and avg_arousal is not None:
            # Negative emotions with high arousal indicate stress
            if avg_valence < -0.3 and avg_arousal > 0.7:
                risk_score += 0.2
            # Positive emotions with moderate arousal are good
            elif avg_valence > 0.3 and 0.3 <= avg_arousal <= 0.7:
                risk_score -= 0.1
        
        # Specific emotion-based adjustments
        high_risk_emotions = ['anger', 'fear', 'sadness', 'stress']
        low_risk_emotions = ['joy', 'contentment', 'calm', 'confident']
        
        if last_emotion in high_risk_emotions:
            risk_score += 0.15
        elif last_emotion in low_risk_emotions:
            risk_score -= 0.1
        
        # Add some controlled randomness for realistic variance
        risk_score += random.uniform(-0.05, 0.05)
        
        # Ensure score is within valid range
        risk_score = max(0.0, min(1.0, risk_score + 0.4))  # Base score of 0.4
        
        return round(risk_score, 3)
    
    def _get_fallback_prediction(self, features: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Get fallback prediction with proper metadata"""
        try:
            fallback_score = self._fallback_risk_score(features)
            self.performance_metrics['fallback_predictions'] += 1
            
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time)
            
            logger.info(f"Fallback prediction completed in {response_time:.3f}s")
            
            return {
                'risk_score': fallback_score,
                'model_version': 'fallback_v1.0',
                'prediction_source': 'fallback_algorithm',
                'circuit_breaker_state': self.circuit_breaker.state.value,
                'response_time': response_time,
                'features_used': list(features.keys()),
                'fallback_reason': 'ml_service_unavailable'
            }
            
        except Exception as e:
            logger.error(f"Fallback prediction failed: {e}")
            # Ultimate fallback - conservative risk score
            return {
                'risk_score': 0.7,  # Conservative high-risk score
                'model_version': 'emergency_fallback',
                'prediction_source': 'emergency_fallback',
                'circuit_breaker_state': self.circuit_breaker.state.value,
                'response_time': time.time() - start_time,
                'features_used': [],
                'fallback_reason': 'all_systems_failed'
            }
    
    def _update_performance_metrics(self, response_time: float):
        """Update performance metrics"""
        current_avg = self.performance_metrics['average_response_time']
        total_predictions = self.performance_metrics['total_predictions']
        
        # Calculate new average response time
        new_avg = ((current_avg * (total_predictions - 1)) + response_time) / total_predictions
        self.performance_metrics['average_response_time'] = new_avg
        self.performance_metrics['last_prediction_time'] = datetime.now()
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health information"""
        circuit_status = self.circuit_breaker.get_status()
        
        # Calculate health score
        health_score = self._calculate_health_score()
        
        return {
            'service_name': 'ml_model_service',
            'health_score': health_score,
            'status': self._get_health_status(health_score),
            'circuit_breaker': circuit_status,
            'performance_metrics': self.performance_metrics.copy(),
            'recommendations': self._get_health_recommendations(health_score)
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall service health score (0-100)"""
        score = 100.0
        
        # Circuit breaker state impact
        if self.circuit_breaker.is_open:
            score -= 40
        elif self.circuit_breaker.is_half_open:
            score -= 20
        
        # Failure rate impact
        failure_rate = self.circuit_breaker.metrics.recent_failure_rate
        score -= (failure_rate * 30)
        
        # Fallback usage impact
        if self.performance_metrics['total_predictions'] > 0:
            fallback_rate = (self.performance_metrics['fallback_predictions'] / 
                           self.performance_metrics['total_predictions'])
            score -= (fallback_rate * 20)
        
        # Response time impact
        avg_response = self.performance_metrics['average_response_time']
        if avg_response > 2.0:
            score -= min(10, (avg_response - 2.0) * 5)
        
        return max(0.0, min(100.0, score))
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 50:
            return "degraded"
        elif health_score >= 25:
            return "poor"
        else:
            return "critical"
    
    def _get_health_recommendations(self, health_score: float) -> list:
        """Get recommendations based on health score"""
        recommendations = []
        
        if self.circuit_breaker.is_open:
            recommendations.append("Circuit breaker is open - investigate ML service issues")
        
        failure_rate = self.circuit_breaker.metrics.recent_failure_rate
        if failure_rate > 0.2:
            recommendations.append(f"High failure rate ({failure_rate:.1%}) - check ML service stability")
        
        if self.performance_metrics['total_predictions'] > 0:
            fallback_rate = (self.performance_metrics['fallback_predictions'] / 
                           self.performance_metrics['total_predictions'])
            if fallback_rate > 0.3:
                recommendations.append(f"High fallback usage ({fallback_rate:.1%}) - ML service may be unreliable")
        
        avg_response = self.performance_metrics['average_response_time']
        if avg_response > 3.0:
            recommendations.append(f"Slow response times ({avg_response:.2f}s) - consider service optimization")
        
        if not recommendations:
            recommendations.append("Service is operating normally")
        
        return recommendations
    
    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker"""
        self.circuit_breaker.reset()
        logger.info("ML model service circuit breaker manually reset")
    
    def force_circuit_open(self):
        """Manually force circuit breaker open (for maintenance)"""
        self.circuit_breaker.force_open()
        logger.warning("ML model service circuit breaker manually opened")


# Global instance (singleton pattern)
_protected_ml_service = None


def get_protected_ml_service() -> ProtectedMLModelService:
    """
    Get the singleton instance of the protected ML service
    
    Returns:
        ProtectedMLModelService instance with circuit breaker protection
    """
    global _protected_ml_service
    if _protected_ml_service is None:
        _protected_ml_service = ProtectedMLModelService()
    return _protected_ml_service


def get_protected_risk_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for getting protected risk score
    
    This function provides the same interface as the original ML model
    but with circuit breaker protection and fallback mechanisms.
    
    Args:
        features: Dictionary of financial and emotional features
        
    Returns:
        Dictionary containing risk score and prediction metadata
    """
    service = get_protected_ml_service()
    return service.predict_risk_score(features)
