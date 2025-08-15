#!/usr/bin/env python3
"""
Quick Manual Test for ML Model Integration

Simple script to manually test the ML model without complex setup.
Run this from the project root directory.
"""

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    print("🧪 Quick ML Model Test")
    print("-" * 30)
    
    try:
        # Import the ML model
        from app.ml.model import get_credit_risk_score, get_credit_risk_model
        
        print("✅ ML Model imports successful")
        
        # Test with sample features
        test_features = {
            "transaction_count": 12,
            "avg_transaction_amount": 300.75,
            "current_credit_limit": 1500.0,
            "avg_valence": 0.2,  # Slightly positive mood
            "avg_arousal": 0.5,   # Moderate arousal
            "last_emotion": "happy"
        }
        
        print(f"\n📊 Test Features:")
        for key, value in test_features.items():
            print(f"  {key}: {value}")
        
        # Get risk score
        risk_score = get_credit_risk_score(test_features)
        
        print(f"\n🎯 Results:")
        print(f"  Risk Score: {risk_score}")
        print(f"  Risk Level: {'LOW' if risk_score < 0.3 else 'MEDIUM' if risk_score < 0.6 else 'HIGH'}")
        print(f"  Would Approve: {'YES' if risk_score < 0.6 else 'NO'}")
        
        # Test model info
        model = get_credit_risk_model()
        info = model.get_model_info()
        
        print(f"\n🔧 Model Info:")
        print(f"  Version: {info['model_version']}")
        print(f"  Features: {info['feature_count']}")
        print(f"  Expected Features: {', '.join(info['features'])}")
        
        # Test multiple calls to show randomness
        print(f"\n🎲 Randomness Test (5 calls):")
        for i in range(5):
            score = get_credit_risk_score(test_features)
            print(f"  Call {i+1}: {score}")
        
        print("\n✅ ML Model integration is working correctly!")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
    
    sys.exit(0 if success else 1)
