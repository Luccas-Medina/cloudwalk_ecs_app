#!/usr/bin/env python3
"""
CloudWalk ECS App - System Verification Script
==============================================

This script performs comprehensive system verification to ensure all 
CloudWalk ECS App functionalities are working correctly.

Usage:
    python verify_system.py

Requirements:
    - Docker Compose services running (run: docker-compose up -d)
    - Python dependencies installed (websockets, requests)
    - Backend accessible on localhost:8000

The script tests:
    ✅ Core Systems (Backend, Dashboard)
    ✅ Credit Evaluation & Deployment 
    ✅ Real-time Emotion Processing
    ✅ WebSocket Connections
    ✅ API Integrations
    ✅ Background Task Processing

Exit Codes:
    0 - All systems operational
    1 - Some systems failed verification
"""

import asyncio
import requests
import json
import websockets
import base64
from datetime import datetime

class FinalVerificationReport:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = "dev_ingest_token_please_change"
        self.results = {}
        
        # Setup Basic Auth for protected endpoints
        credentials = base64.b64encode(b"admin:test").decode("ascii")
        self.auth_headers = {"Authorization": f"Basic {credentials}"}
        
    def print_header(self):
        print("=" * 70)
        print("🚀 CLOUDWALK ECS APP - FINAL VERIFICATION REPORT")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 70)
    
    def test_core_systems(self):
        print("\n📋 CORE SYSTEMS VERIFICATION")
        print("-" * 40)
        
        # 1. Backend Health
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend Health: {data['message']} v{data['version']}")
                self.results["backend"] = "✅ OPERATIONAL"
            else:
                print(f"❌ Backend Health: Status {response.status_code}")
                self.results["backend"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ Backend Health: {e}")
            self.results["backend"] = "❌ FAILED"
        
        # 2. Dashboard Access
        try:
            response = requests.get(f"{self.base_url}/dashboard")
            if response.status_code == 200 and "Emotion Processing" in response.text:
                print("✅ Dashboard: Accessible and responsive")
                self.results["dashboard"] = "✅ OPERATIONAL"
            else:
                print(f"❌ Dashboard: Status {response.status_code}")
                self.results["dashboard"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ Dashboard: {e}")
            self.results["dashboard"] = "❌ FAILED"
    
    def test_credit_system(self):
        print("\n💳 CREDIT SYSTEM VERIFICATION")
        print("-" * 40)
        
        # Test Credit Evaluation
        try:
            payload = {"user_id": 999, "amount": 10000, "purpose": "business_expansion"}
            response = requests.post(
                f"{self.base_url}/credit/evaluate/999", 
                json=payload,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                print(f"✅ Credit Evaluation: Task {task_id}")
                self.results["credit_evaluation"] = "✅ OPERATIONAL"
            else:
                print(f"❌ Credit Evaluation: Status {response.status_code}")
                self.results["credit_evaluation"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ Credit Evaluation: {e}")
            self.results["credit_evaluation"] = "❌ FAILED"
        
        # Test Credit Deployment
        try:
            # Create offer
            offer_payload = {
                "user_id": 999,
                "credit_limit": 25000,
                "offered_limit": 25000,
                "interest_rate": 0.035,  # 3.5% as decimal
                "term_months": 18,
                "offer_type": "business_credit",
                "model_version": "v1.0",
                "risk_assessment": {"score": 0.75, "level": "medium"},
                "offer_expires_at": "2025-12-31T23:59:59"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/credit/offers", 
                json=offer_payload,
                headers=self.auth_headers
            )
            
            if response.status_code == 201:
                data = response.json()
                offer_id = data.get("offer_id") or data.get("id")
                print(f"✅ Credit Deployment - Create: Offer {offer_id}")
                print(f"    Response data: {data}")
                
                if offer_id:
                    # Accept offer
                    accept_payload = {"user_id": 999, "terms_accepted": True}
                    accept_response = requests.post(
                        f"{self.base_url}/api/v1/credit/offers/{offer_id}/accept",
                        json=accept_payload,
                        headers=self.auth_headers
                    )
                    
                    if accept_response.status_code == 200:
                        print("✅ Credit Deployment - Accept: Successful")
                        self.results["credit_deployment"] = "✅ OPERATIONAL"
                    else:
                        print(f"❌ Credit Deployment - Accept: Status {accept_response.status_code}")
                        try:
                            error_data = accept_response.json()
                            print(f"    Error: {error_data}")
                        except:
                            print(f"    Error text: {accept_response.text}")
                        self.results["credit_deployment"] = "❌ PARTIAL"
                else:
                    print("❌ Credit Deployment - Accept: No offer_id received")
                    self.results["credit_deployment"] = "❌ PARTIAL"
            else:
                print(f"❌ Credit Deployment - Create: Status {response.status_code}")
                self.results["credit_deployment"] = "❌ FAILED"
        except Exception as e:
            print(f"❌ Credit Deployment: {e}")
            self.results["credit_deployment"] = "❌ FAILED"
    
    async def test_emotion_system(self):
        print("\n🧠 EMOTION PROCESSING VERIFICATION")
        print("-" * 40)
        
        try:
            # Test Metrics WebSocket
            metrics_uri = f"ws://localhost:8000/ws/emotions/metrics?token={self.token}"
            async with websockets.connect(metrics_uri) as websocket:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if "metrics" in data:
                    metrics = data["metrics"]
                    print(f"✅ Emotion Metrics: {metrics.get('total_events')} events tracked")
                    self.results["emotion_metrics"] = "✅ OPERATIONAL"
                else:
                    print("❌ Emotion Metrics: Invalid format")
                    self.results["emotion_metrics"] = "❌ FAILED"
            
            # Test Emotion Stream
            stream_uri = f"ws://localhost:8000/ws/emotions/stream?user_id=999&session_id=final_test&token={self.token}"
            async with websockets.connect(stream_uri) as websocket:
                # Wait for welcome
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome)
                
                if welcome_data.get("status") == "connected":
                    print("✅ Emotion Stream: Connection established")
                    
                    # Send test event
                    test_event = {
                        "user_id": 999,
                        "emotion_label": "joy",  # Using valid emotion from the enum list
                        "valence": 0.9,
                        "arousal": 0.8,
                        "source": "physiological",
                        "confidence": 0.95
                    }
                    
                    await websocket.send(json.dumps(test_event))
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("status") == "processed":
                        print(f"✅ Emotion Processing: Event processed successfully")
                        self.results["emotion_processing"] = "✅ OPERATIONAL"
                    else:
                        print(f"❌ Emotion Processing: Event not processed - {response_data}")
                        self.results["emotion_processing"] = "❌ FAILED"
                else:
                    print("❌ Emotion Stream: Connection failed")
                    self.results["emotion_processing"] = "❌ FAILED"
                    
        except Exception as e:
            print(f"❌ Emotion System: {e}")
            self.results["emotion_metrics"] = "❌ FAILED"
            self.results["emotion_processing"] = "❌ FAILED"
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 FINAL VERIFICATION SUMMARY")
        print("=" * 70)
        
        total_systems = len(self.results)
        operational_systems = sum(1 for result in self.results.values() if "✅" in result)
        
        for system, status in self.results.items():
            print(f"{status} {system.replace('_', ' ').title()}")
        
        print("-" * 70)
        print(f"📈 System Status: {operational_systems}/{total_systems} systems operational")
        
        if operational_systems == total_systems:
            print("🎉 ALL SYSTEMS OPERATIONAL - READY FOR PRODUCTION")
            print("✅ Repository commit approved")
        else:
            print("⚠️  Some systems need attention before production deployment")
            
        print("=" * 70)
    
    async def run_verification(self):
        self.print_header()
        self.test_core_systems()
        self.test_credit_system()
        await self.test_emotion_system()
        self.print_summary()
        
        return sum(1 for result in self.results.values() if "✅" in result) == len(self.results)

async def main():
    verifier = FinalVerificationReport()
    success = await verifier.run_verification()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
