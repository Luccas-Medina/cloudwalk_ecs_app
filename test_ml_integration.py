#!/usr/bin/env python3
"""
Test script for ML Model Integration in CloudWalk ECS

This script comprehensively tests:
1. ML Model Interface
2. Credit Service Integration  
3. API Endpoint Integration
4. End-to-End Credit Evaluation

Usage:
    python test_ml_integration.py
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Any

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_ml_model_direct():
    """Test 1: Direct ML Model Interface"""
    print("🧪 Test 1: Direct ML Model Interface")
    print("-" * 50)
    
    try:
        from app.ml.model import get_credit_risk_score, get_credit_risk_model
        
        # Test basic functionality
        features = {
            "transaction_count": 15,
            "avg_transaction_amount": 250.50,
            "current_credit_limit": 2000.0,
            "avg_valence": 0.3,
            "avg_arousal": 0.4,
            "last_emotion": "happy"
        }
        
        print(f"Input features: {json.dumps(features, indent=2)}")
        
        # Test convenience function
        risk_score = get_credit_risk_score(features)
        print(f"✅ Risk Score: {risk_score}")
        print(f"✅ Score Type: {type(risk_score)}")
        print(f"✅ Score Range: {'VALID' if 0.0 <= risk_score <= 1.0 else 'INVALID'}")
        
        # Test model class interface
        model = get_credit_risk_model()
        model_info = model.get_model_info()
        print(f"✅ Model Info: {json.dumps(model_info, indent=2)}")
        
        # Test multiple calls for consistency
        scores = [get_credit_risk_score(features) for _ in range(5)]
        print(f"✅ Multiple calls: {scores}")
        print(f"✅ Randomness verified: {'YES' if len(set(scores)) > 1 else 'NO'}")
        
    except Exception as e:
        print(f"❌ ML Model Test Failed: {e}")
        return False
    
    print("✅ ML Model Direct Test: PASSED\n")
    return True


def test_credit_service_integration():
    """Test 2: Credit Service Integration"""
    print("🧪 Test 2: Credit Service Integration")
    print("-" * 50)
    
    try:
        from app.services.credit_service import calculate_credit_offer
        from app.db import SessionLocal
        from app.models import User, Transaction, EmotionalEvent
        from sqlalchemy import func
        
        # Mock user ID (assuming test data exists)
        test_user_id = 1
        
        print(f"Testing credit calculation for user_id: {test_user_id}")
        
        result = calculate_credit_offer(test_user_id)
        
        print(f"✅ Credit Result: {json.dumps(result, indent=2, default=str)}")
        
        # Validate result structure
        required_fields = ["approved", "risk_score", "new_credit_limit", "interest_rate", "credit_type", "features_used"]
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        
        # Validate data types and ranges
        assert isinstance(result["approved"], bool), "approved should be boolean"
        assert isinstance(result["risk_score"], float), "risk_score should be float"
        assert 0.0 <= result["risk_score"] <= 1.0, "risk_score should be 0-1"
        assert isinstance(result["new_credit_limit"], (int, float)), "credit_limit should be numeric"
        assert isinstance(result["interest_rate"], (int, float)), "interest_rate should be numeric"
        
        print("✅ Data validation passed")
        
    except Exception as e:
        print(f"❌ Credit Service Test Failed: {e}")
        return False
    
    print("✅ Credit Service Integration Test: PASSED\n")
    return True


def test_api_endpoint_integration():
    """Test 3: API Endpoint Integration"""
    print("🧪 Test 3: API Endpoint Integration")
    print("-" * 50)
    
    base_url = "http://localhost:8000"
    test_user_id = 1
    
    try:
        # Test credit evaluation endpoint
        print(f"Testing POST {base_url}/credit/evaluate/{test_user_id}")
        
        response = requests.post(f"{base_url}/credit/evaluate/{test_user_id}", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
        
        eval_data = response.json()
        print(f"✅ Evaluation Response: {json.dumps(eval_data, indent=2)}")
        
        # Get task ID for status checking
        task_id = eval_data.get("task_id")
        if not task_id:
            print("❌ No task_id in response")
            return False
        
        # Wait and check task status
        print(f"Checking task status: {task_id}")
        time.sleep(2)  # Allow task to process
        
        status_response = requests.get(f"{base_url}/credit/status/{task_id}", timeout=10)
        
        if status_response.status_code != 200:
            print(f"❌ Status API Error: {status_response.status_code}")
            return False
        
        status_data = status_response.json()
        print(f"✅ Task Status: {json.dumps(status_data, indent=2)}")
        
        # Check if task completed successfully
        if status_data.get("status") == "success":
            result = status_data.get("result", {})
            if "credit_evaluation" in result:
                print("✅ ML Model integrated in Celery task successfully")
            else:
                print("❌ Credit evaluation missing from result")
                return False
        else:
            print(f"⏳ Task status: {status_data.get('status')}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure Docker services are running:")
        print("   docker-compose -f infra/docker-compose.yml up -d")
        return False
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False
    
    print("✅ API Endpoint Integration Test: PASSED\n")
    return True


def test_edge_cases():
    """Test 4: Edge Cases and Error Handling"""
    print("🧪 Test 4: Edge Cases and Error Handling")
    print("-" * 50)
    
    try:
        from app.ml.model import get_credit_risk_score
        
        # Test with minimal features
        minimal_features = {}
        score1 = get_credit_risk_score(minimal_features)
        print(f"✅ Empty features: {score1}")
        
        # Test with missing features
        partial_features = {"transaction_count": 5}
        score2 = get_credit_risk_score(partial_features)
        print(f"✅ Partial features: {score2}")
        
        # Test with invalid data types
        invalid_features = {
            "transaction_count": "invalid",
            "avg_valence": None,
            "last_emotion": 123
        }
        score3 = get_credit_risk_score(invalid_features)
        print(f"✅ Invalid features handled: {score3}")
        
        # All should return valid scores
        for i, score in enumerate([score1, score2, score3], 1):
            assert 0.0 <= score <= 1.0, f"Score {i} out of range: {score}"
        
        print("✅ Edge cases handled properly")
        
    except Exception as e:
        print(f"❌ Edge Case Test Failed: {e}")
        return False
    
    print("✅ Edge Cases Test: PASSED\n")
    return True


def test_performance():
    """Test 5: Performance and Consistency"""
    print("🧪 Test 5: Performance and Consistency")
    print("-" * 50)
    
    try:
        from app.ml.model import get_credit_risk_score
        import time
        
        features = {
            "transaction_count": 10,
            "avg_transaction_amount": 150.0,
            "current_credit_limit": 1000.0,
            "avg_valence": 0.2,
            "avg_arousal": 0.3,
            "last_emotion": "neutral"
        }
        
        # Performance test
        start_time = time.time()
        scores = []
        for _ in range(100):
            score = get_credit_risk_score(features)
            scores.append(score)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        print(f"✅ Average call time: {avg_time:.4f} seconds")
        print(f"✅ 100 calls completed in: {end_time - start_time:.4f} seconds")
        
        # Consistency test (all should be different due to randomness)
        unique_scores = len(set(scores))
        print(f"✅ Unique scores out of 100: {unique_scores}")
        print(f"✅ Randomness: {'GOOD' if unique_scores > 80 else 'POOR'}")
        
        # Range validation
        min_score, max_score = min(scores), max(scores)
        print(f"✅ Score range: {min_score:.3f} - {max_score:.3f}")
        
        assert all(0.0 <= score <= 1.0 for score in scores), "Some scores out of range"
        
    except Exception as e:
        print(f"❌ Performance Test Failed: {e}")
        return False
    
    print("✅ Performance Test: PASSED\n")
    return True


def main():
    """Run all ML integration tests"""
    print("🚀 CloudWalk ECS - ML Model Integration Tests")
    print("=" * 60)
    
    tests = [
        test_ml_model_direct,
        test_credit_service_integration,
        test_api_endpoint_integration,
        test_edge_cases,
        test_performance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! ML Model is properly integrated.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
