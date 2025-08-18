# app/ml/model.py
import random
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CreditRiskModel:
    """
    Interface for pre-trained machine learning model integration.
    
    This class provides a clean interface for calling a black-box ML model
    that accepts emotional and financial features and returns a credit risk score.
    """
    
    def __init__(self):
        """Initialize the model interface."""
        self.model_version = "v1.0.0"
        self.feature_schema = self._get_feature_schema()
    
    def predict_risk_score(self, features: Dict) -> float:
        """
        Call the pre-trained ML model to get credit risk score.
        
        Args:
            features (Dict): Processed emotional and financial features
            
        Returns:
            float: Credit risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        # Validate features against expected schema
        validated_features = self._validate_features(features)
        
        # Log model call for monitoring/debugging
        logger.info(f"Calling ML model with features: {list(validated_features.keys())}")
        
        # Mock model call - In production, this would be:
        # - REST API call to ML service
        # - gRPC call to model server  
        # - Direct model inference
        risk_score = self._mock_model_call(validated_features)
        
        logger.info(f"ML model returned risk score: {risk_score}")
        return risk_score
    
    def _mock_model_call(self, features: Dict) -> float:
        """
        Mock the actual ML model call.
        
        In production, this would be replaced with actual model inference:
        - model_client.predict(features)
        - requests.post(MODEL_API_URL, json=features)
        - torch_model(tensor_features)
        """
        # Return random score as specified in requirements
        return round(random.uniform(0.0, 1.0), 3)
    
    def _validate_features(self, features: Dict) -> Dict:
        """
        Validate and normalize input features according to model schema.
        
        This ensures the model receives features in the expected format,
        handling missing values and type conversions.
        """
        validated = {}
        
        for feature_name, config in self.feature_schema.items():
            value = features.get(feature_name, config['default'])
            
            # Type conversion and validation
            if config['type'] == 'numeric':
                try:
                    validated[feature_name] = float(value) if value is not None else config['default']
                except (ValueError, TypeError):
                    validated[feature_name] = config['default']
            elif config['type'] == 'categorical':
                validated[feature_name] = str(value) if value is not None else config['default']
        
        return validated
    
    def _get_feature_schema(self) -> Dict:
        """
        Define the expected feature schema for the ML model.
        
        This documents which features the model expects and their types,
        ensuring consistency between data processing and model input.
        """
        return {
            # Financial Features
            "transaction_count": {
                "type": "numeric",
                "description": "Total number of user transactions",
                "default": 0.0
            },
            "avg_transaction_amount": {
                "type": "numeric", 
                "description": "Average transaction amount",
                "default": 0.0
            },
            "current_credit_limit": {
                "type": "numeric",
                "description": "User's current credit limit",
                "default": 0.0
            },
            
            # Emotional Features  
            "avg_valence": {
                "type": "numeric",
                "description": "Average emotional valence (-1 to 1)",
                "default": 0.0
            },
            "avg_arousal": {
                "type": "numeric", 
                "description": "Average emotional arousal (0 to 1)",
                "default": 0.0
            },
            "last_emotion": {
                "type": "categorical",
                "description": "Most recent emotion label",
                "default": "neutral"
            }
        }
    
    def get_model_info(self) -> Dict:
        """
        Return information about the model for debugging and monitoring.
        """
        return {
            "model_version": self.model_version,
            "feature_count": len(self.feature_schema),
            "features": list(self.feature_schema.keys()),
            "description": "Pre-trained credit risk assessment model"
        }


# Global model instance (singleton pattern)
_model_instance = None

def get_credit_risk_model() -> CreditRiskModel:
    """
    Get the singleton instance of the credit risk model.
    
    This ensures consistent model interface across the application.
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = CreditRiskModel()
    return _model_instance


def get_credit_risk_score(features: Dict) -> float:
    """
    Convenience function for getting credit risk score.
    
    This maintains backward compatibility with existing code
    while providing access to the enhanced model interface.
    
    Args:
        features (Dict): Financial and emotional features
        
    Returns:
        float: Credit risk score (0.0 = low risk, 1.0 = high risk)
    """
    model = get_credit_risk_model()
    return model.predict_risk_score(features)
