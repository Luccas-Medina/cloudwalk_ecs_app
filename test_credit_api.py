#!/usr/bin/env python3
"""
Credit Limit API Requirements Test

This script tests the Credit Limit API against the specific requirements:
1) The ML model result and approval decision
2) The credit limit and interest rate
3) Credit type (Short-Term, Long-Term)
"""

import requests
import json
import sys

def test_credit_limit_api():
    """Test the Credit Limit API against requirements"""
    
    base_url = "http://localhost:8000"
    user_id = 1
    
    print("🧪 Testing Credit Limit API Requirements")
    print("=" * 50)
    
    try:
        # Test the main Credit Limit API endpoint
        print("📡 Testing POST /credit/calculate/{user_id}")
        response = requests.post(f"{base_url}/credit/calculate/{user_id}", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print("✅ API Response received")
        print(json.dumps(data, indent=2))
        print()
        
        # Verify Requirement 1: ML Model Result
        print("🔍 Requirement 1: ML Model Result")
        ml_result = data.get("ml_model_result", {})
        
        if "risk_score" in ml_result and "approval_decision" in ml_result:
            risk_score = ml_result["risk_score"]
            approval = ml_result["approval_decision"]
            print(f"✅ Risk Score: {risk_score}")
            print(f"✅ Approval Decision: {approval}")
            print(f"✅ Model Version: {ml_result.get('model_version')}")
            print(f"✅ Features Processed: {len(ml_result.get('features_processed', {}))}")
        else:
            print("❌ Missing ML model result data")
            return False
        
        print()
        
        # Verify Requirement 2: Credit Limit and Interest Rate
        print("🔍 Requirement 2: Credit Limit and Interest Rate")
        credit_offer = data.get("credit_offer")
        
        if data.get("approved") and credit_offer:
            print(f"✅ Credit Limit: ${credit_offer.get('credit_limit')}")
            print(f"✅ Interest Rate: {credit_offer.get('interest_rate'):.4f} ({credit_offer.get('interest_rate')*100:.2f}%)")
            
            # Validate reasonable ranges
            credit_limit = credit_offer.get('credit_limit', 0)
            interest_rate = credit_offer.get('interest_rate', 0)
            
            if 0 < credit_limit <= 100000:
                print("✅ Credit limit in reasonable range")
            else:
                print(f"⚠️ Credit limit seems unusual: ${credit_limit}")
            
            if 0.10 <= interest_rate <= 0.30:
                print("✅ Interest rate in reasonable range")
            else:
                print(f"⚠️ Interest rate seems unusual: {interest_rate:.4f}")
                
        elif not data.get("approved"):
            print("✅ Credit denied - no credit limit/interest rate (correct)")
        else:
            print("❌ Missing credit offer data for approved application")
            return False
        
        print()
        
        # Verify Requirement 3: Credit Type
        print("🔍 Requirement 3: Credit Type")
        if credit_offer:
            credit_type = credit_offer.get("credit_type")
            valid_types = ["Short-Term", "Long-Term"]
            
            if credit_type in valid_types:
                print(f"✅ Credit Type: {credit_type}")
            else:
                print(f"❌ Invalid credit type: {credit_type}")
                print(f"Expected one of: {valid_types}")
                return False
        else:
            # For rejected applications
            print("✅ No credit type for rejected application (correct)")
        
        print()
        print("🎯 API Requirements Summary:")
        print(f"✅ Requirement 1: ML model result ✓")
        print(f"✅ Requirement 2: Credit limit and interest rate ✓")
        print(f"✅ Requirement 3: Credit type ✓")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure services are running:")
        print("   cd infra && docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_multiple_scenarios():
    """Test multiple scenarios to verify different outcomes"""
    
    print("\n🔄 Testing Multiple Scenarios")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    for i in range(3):
        print(f"\n📊 Scenario {i+1}:")
        try:
            response = requests.post(f"{base_url}/credit/calculate/1", timeout=10)
            data = response.json()
            
            risk_score = data["ml_model_result"]["risk_score"]
            approved = data["approved"]
            credit_type = data.get("credit_offer", {}).get("credit_type", "N/A")
            
            print(f"  Risk Score: {risk_score:.3f}")
            print(f"  Approved: {approved}")
            print(f"  Credit Type: {credit_type}")
            
        except Exception as e:
            print(f"  ❌ Scenario {i+1} failed: {e}")

def test_demo_endpoint():
    """Test the demo endpoint for comprehensive view"""
    
    print("\n🎬 Testing Demo Endpoint")
    print("=" * 25)
    
    try:
        response = requests.get("http://localhost:8000/credit/demo/1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Demo endpoint working")
            print("📋 Demo shows:")
            print(f"  - ML Model: {data.get('1_ml_model_result', {}).get('risk_score')}")
            print(f"  - Credit Terms: ${data.get('2_financial_terms', {}).get('credit_limit')}")
            print(f"  - Credit Type: {data.get('3_credit_type', {}).get('type')}")
        else:
            print(f"❌ Demo endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Demo test failed: {e}")

def main():
    """Run all Credit Limit API tests"""
    
    print("🚀 CloudWalk Credit Limit API - Requirements Test")
    print("=" * 55)
    
    # Test main requirements
    success = test_credit_limit_api()
    
    if success:
        # Test additional scenarios
        test_multiple_scenarios()
        test_demo_endpoint()
        
        print("\n🎉 ALL CREDIT LIMIT API REQUIREMENTS MET!")
        print("✅ 1) ML model result - IMPLEMENTED")
        print("✅ 2) Credit limit and interest rate - IMPLEMENTED") 
        print("✅ 3) Credit type (Short-Term/Long-Term) - IMPLEMENTED")
        
    else:
        print("\n❌ Some requirements not met. Check output above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
