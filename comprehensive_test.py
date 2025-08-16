#!/usr/bin/env python3
"""
Comprehensive test suite for CloudWalk ECS App
Tests all major functionalities before repository commit
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime

class CloudWalkTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = "dev_ingest_token_please_change"
        self.test_results = {}
        
    def log_test(self, test_name, status, details=""):
        """Log test result"""
        symbol = "✅" if status else "❌"
        print(f"{symbol} {test_name}: {details}")
        self.test_results[test_name] = {"status": status, "details": details}
        
    def test_backend_health(self):
        """Test basic backend connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200 and "CloudWalk" in response.text:
                self.log_test("Backend Health", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Backend Health", False, f"Unexpected response: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", False, f"Connection failed: {e}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard accessibility"""
        try:
            response = requests.get(f"{self.base_url}/dashboard", timeout=5)
            if response.status_code == 200 and "Emotion Processing" in response.text:
                self.log_test("Dashboard Access", True, "Dashboard loads successfully")
                return True
            else:
                self.log_test("Dashboard Access", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dashboard Access", False, f"Failed: {e}")
            return False
    
    def test_credit_evaluation(self):
        """Test credit evaluation system"""
        try:
            # Test credit evaluation endpoint - note it expects user_id in URL
            test_user_id = 123
            response = requests.post(
                f"{self.base_url}/credit/evaluate/{test_user_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    self.log_test("Credit Evaluation", True, f"Task ID: {data['task_id']}")
                    return True
                else:
                    self.log_test("Credit Evaluation", False, "No task_id in response")
                    return False
            else:
                self.log_test("Credit Evaluation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Credit Evaluation", False, f"Failed: {e}")
            return False
    
    def test_credit_deployment(self):
        """Test credit deployment system"""
        try:
            # Test credit deployment endpoints
            
            # 1. Create credit offer
            offer_payload = {
                "user_id": 123,
                "offered_limit": 15000.0,
                "interest_rate": 0.025,  # 2.5% as decimal
                "model_version": "v2.0.0",
                "risk_assessment": {
                    "risk_score": 0.3,
                    "approval_probability": 0.85,
                    "factors": ["stable_income", "good_payment_history"]
                },
                "emotional_context": {
                    "avg_sentiment": 0.7,
                    "stress_indicators": [],
                    "confidence_level": 0.8
                },
                "expires_in_hours": 72
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/credit/offers",
                json=offer_payload,
                timeout=10
            )
            
            if response.status_code != 201:  # Credit offer creation returns 201 Created
                self.log_test("Credit Deployment - Create Offer", False, f"Status: {response.status_code}")
                return False
            
            offer_data = response.json()
            offer_id = offer_data.get("id")  # API returns "id", not "offer_id"
            
            if not offer_id:
                self.log_test("Credit Deployment - Create Offer", False, "No offer_id returned")
                return False
            
            self.log_test("Credit Deployment - Create Offer", True, f"Offer ID: {offer_id}")
            
            # 2. Accept credit offer
            acceptance_payload = {
                "user_id": 123,
                "terms_accepted": True,
                "device_info": {
                    "platform": "test",
                    "app_version": "1.0.0"
                }
            }
            
            accept_response = requests.post(
                f"{self.base_url}/api/v1/credit/offers/{offer_id}/accept",
                json=acceptance_payload,
                timeout=10
            )
            
            if accept_response.status_code == 200:
                self.log_test("Credit Deployment - Accept Offer", True, "Offer accepted successfully")
                return True
            else:
                self.log_test("Credit Deployment - Accept Offer", False, f"Status: {accept_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Credit Deployment", False, f"Failed: {e}")
            return False
    
    async def test_emotion_websockets(self):
        """Test emotion WebSocket functionality"""
        try:
            # Test metrics WebSocket
            metrics_uri = f"ws://localhost:8000/ws/emotions/metrics?token={self.token}"
            
            async with websockets.connect(metrics_uri) as websocket:
                # Wait for first metrics message
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                
                if "metrics" in data and "timestamp" in data:
                    self.log_test("Emotion Metrics WebSocket", True, "Metrics received successfully")
                else:
                    self.log_test("Emotion Metrics WebSocket", False, "Invalid metrics format")
                    return False
            
            # Test emotion stream WebSocket
            stream_uri = f"ws://localhost:8000/ws/emotions/stream?user_id=999&session_id=test_session&token={self.token}"
            
            async with websockets.connect(stream_uri) as websocket:
                # Wait for welcome message
                welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                welcome_data = json.loads(welcome)
                
                if welcome_data.get("status") == "connected":
                    self.log_test("Emotion Stream WebSocket", True, "Connection established")
                    
                    # Send test emotion event
                    test_event = {
                        "user_id": 999,
                        "emotion_label": "joy",
                        "valence": 0.8,
                        "arousal": 0.7,
                        "source": "facial",
                        "confidence": 0.9
                    }
                    
                    await websocket.send(json.dumps(test_event))
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("status") == "processed":
                        self.log_test("Emotion Event Processing", True, f"Task ID: {response_data.get('task_id')}")
                        return True
                    else:
                        self.log_test("Emotion Event Processing", False, "Event not processed")
                        return False
                else:
                    self.log_test("Emotion Stream WebSocket", False, "Connection failed")
                    return False
                    
        except Exception as e:
            self.log_test("Emotion WebSockets", False, f"Failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test various API endpoints"""
        endpoints_to_test = [
            ("/credit/status", "Credit Status"),
            ("/api/v1/credit/users/123/summary", "User Credit Summary"),
        ]
        
        all_passed = True
        
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 404]:  # 404 is acceptable for non-existent users
                    self.log_test(f"API - {name}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"API - {name}", False, f"Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"API - {name}", False, f"Failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting CloudWalk ECS App Comprehensive Test Suite")
        print("=" * 60)
        
        # Test 1: Backend Health
        print("\n📋 Testing Backend Health...")
        if not self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return False
        
        # Test 2: Dashboard Access
        print("\n📋 Testing Dashboard Access...")
        self.test_dashboard_access()
        
        # Test 3: API Endpoints
        print("\n📋 Testing API Endpoints...")
        self.test_api_endpoints()
        
        # Test 4: Credit Evaluation
        print("\n📋 Testing Credit Evaluation...")
        self.test_credit_evaluation()
        
        # Test 5: Credit Deployment
        print("\n📋 Testing Credit Deployment...")
        self.test_credit_deployment()
        
        # Test 6: Emotion WebSockets
        print("\n📋 Testing Emotion WebSockets...")
        await self.test_emotion_websockets()
        
        # Test Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result["status"])
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            symbol = "✅" if result["status"] else "❌"
            print(f"{symbol} {test_name}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Ready for repository commit.")
            return True
        else:
            print("⚠️  Some tests failed. Please review before committing.")
            return False

async def main():
    tester = CloudWalkTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())
