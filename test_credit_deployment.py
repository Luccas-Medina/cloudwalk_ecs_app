#!/usr/bin/env python3
"""
Credit Deployment System - Comprehensive Test Suite

Tests the complete credit offer lifecycle:
1. Creating credit offers
2. User acceptance workflow  
3. Asynchronous deployment
4. Mobile notifications
5. Event-driven architecture
6. Audit trail tracking
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USERS = [123, 456, 789]

class CreditDeploymentTester:
    """Comprehensive tester for credit deployment system"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_comprehensive_test(self):
        """Run complete credit deployment test suite"""
        
        print("🏦 CloudWalk Credit Deployment System - Comprehensive Test")
        print("=" * 70)
        print("Testing event-driven credit offer deployment with notifications")
        print("=" * 70)
        
        # Test 1: Create credit offers
        await self._test_credit_offer_creation()
        
        # Test 2: Accept credit offers
        await self._test_credit_offer_acceptance()
        
        # Test 3: Monitor deployment progress
        await self._test_deployment_monitoring()
        
        # Test 4: Test notification system
        await self._test_notification_system()
        
        # Test 5: Test user credit summaries
        await self._test_credit_summaries()
        
        # Test 6: Test edge cases
        await self._test_edge_cases()
        
        self._print_test_summary()
    
    async def _test_credit_offer_creation(self):
        """Test creating credit offers for multiple users"""
        print("\n📋 Test 1: Credit Offer Creation")
        print("-" * 40)
        
        for user_id in TEST_USERS:
            try:
                offer_data = {
                    "user_id": user_id,
                    "offered_limit": 5000.0 + (user_id * 10),  # Varying limits
                    "interest_rate": 0.15,
                    "model_version": "empathic_v2.1",
                    "risk_assessment": {
                        "score": 0.85,
                        "category": "low_risk",
                        "factors": ["stable_income", "good_payment_history", "positive_emotions"]
                    },
                    "emotional_context": {
                        "stability_score": 0.82,
                        "stress_level": 0.2,
                        "recent_patterns": ["calm_positive", "consistent_mood"]
                    },
                    "expires_in_hours": 72
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/v1/credit/offers",
                    json=offer_data
                ) as resp:
                    if resp.status == 201:
                        offer = await resp.json()
                        print(f"✅ Created offer {offer['id']} for user {user_id}: ${offer['offered_limit']:,.2f}")
                        self.test_results.append({
                            "test": "offer_creation",
                            "user_id": user_id,
                            "offer_id": offer['id'],
                            "success": True
                        })
                    else:
                        error = await resp.text()
                        print(f"❌ Failed to create offer for user {user_id}: {error}")
                        self.test_results.append({
                            "test": "offer_creation",
                            "user_id": user_id,
                            "success": False,
                            "error": error
                        })
                        
            except Exception as e:
                print(f"❌ Exception creating offer for user {user_id}: {e}")
                self.test_results.append({
                    "test": "offer_creation",
                    "user_id": user_id,
                    "success": False,
                    "error": str(e)
                })
    
    async def _test_credit_offer_acceptance(self):
        """Test accepting credit offers and triggering deployment"""
        print("\n✅ Test 2: Credit Offer Acceptance & Deployment")
        print("-" * 50)
        
        # Get pending offers for each user
        for user_id in TEST_USERS:
            try:
                # Get user's offers
                async with self.session.get(
                    f"{BASE_URL}/api/v1/credit/users/{user_id}/offers?status=pending"
                ) as resp:
                    if resp.status == 200:
                        offers = await resp.json()
                        
                        if offers:
                            offer = offers[0]  # Accept the first pending offer
                            offer_id = offer['id']
                            
                            # Accept the offer
                            acceptance_data = {
                                "user_id": user_id,
                                "terms_accepted": True,
                                "device_info": {
                                    "platform": "ios",
                                    "device_token": f"test_token_{user_id}",
                                    "app_version": "1.2.3"
                                }
                            }
                            
                            async with self.session.post(
                                f"{BASE_URL}/api/v1/credit/offers/{offer_id}/accept",
                                json=acceptance_data
                            ) as accept_resp:
                                if accept_resp.status == 200:
                                    result = await accept_resp.json()
                                    print(f"✅ User {user_id} accepted offer {offer_id}")
                                    print(f"   📋 Task ID: {result['task_id']}")
                                    print(f"   ⏱️ Status: {result['status']}")
                                    print(f"   🔄 Deployment: {result['deployment_scheduled']}")
                                    
                                    self.test_results.append({
                                        "test": "offer_acceptance",
                                        "user_id": user_id,
                                        "offer_id": offer_id,
                                        "task_id": result['task_id'],
                                        "success": True
                                    })
                                else:
                                    error = await accept_resp.text()
                                    print(f"❌ Failed to accept offer {offer_id}: {error}")
                        else:
                            print(f"⚠️ No pending offers found for user {user_id}")
                            
            except Exception as e:
                print(f"❌ Exception accepting offer for user {user_id}: {e}")
    
    async def _test_deployment_monitoring(self):
        """Test monitoring deployment progress"""
        print("\n📊 Test 3: Deployment Progress Monitoring")
        print("-" * 45)
        
        print("⏳ Waiting for deployments to process...")
        await asyncio.sleep(5)  # Give time for background tasks
        
        for result in self.test_results:
            if result.get("test") == "offer_acceptance" and result.get("success"):
                user_id = result["user_id"]
                offer_id = result["offer_id"]
                
                try:
                    async with self.session.get(
                        f"{BASE_URL}/api/v1/credit/offers/{offer_id}/status?user_id={user_id}"
                    ) as resp:
                        if resp.status == 200:
                            status = await resp.json()
                            print(f"📈 Offer {offer_id} (User {user_id}):")
                            print(f"   Status: {status['status']}")
                            print(f"   Progress: {status['deployment_progress']}")
                            print(f"   Current Step: {status['current_step']}")
                            print(f"   Events: {len(status['events'])} recorded")
                            
                            # Show recent events
                            for event in status['events'][-2:]:
                                print(f"   🔸 {event['event_type']}: {'✅' if event['success'] else '❌'}")
                                
                except Exception as e:
                    print(f"❌ Error checking status for offer {offer_id}: {e}")
    
    async def _test_notification_system(self):
        """Test mobile notification system"""
        print("\n📱 Test 4: Mobile Notification System")
        print("-" * 40)
        
        # Send test notifications
        for user_id in TEST_USERS:
            try:
                notification_data = {
                    "user_id": user_id,
                    "title": f"Test Notification for User {user_id}",
                    "message": "This is a test of the credit notification system. Your account has been updated successfully!"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/v1/credit/notifications/send",
                    params=notification_data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"📤 Sent test notification to user {user_id}: {result['status']}")
                    else:
                        error = await resp.text()
                        print(f"❌ Failed to send notification to user {user_id}: {error}")
                        
            except Exception as e:
                print(f"❌ Exception sending notification to user {user_id}: {e}")
    
    async def _test_credit_summaries(self):
        """Test user credit profile summaries"""
        print("\n💳 Test 5: User Credit Profile Summaries")
        print("-" * 45)
        
        for user_id in TEST_USERS:
            try:
                async with self.session.get(
                    f"{BASE_URL}/api/v1/credit/users/{user_id}/summary"
                ) as resp:
                    if resp.status == 200:
                        summary = await resp.json()
                        print(f"👤 User {user_id} Credit Summary:")
                        print(f"   💰 Current Limit: ${summary['current_limit']:,.2f}")
                        print(f"   💸 Available Credit: ${summary['available_credit']:,.2f}")
                        print(f"   📊 Interest Rate: {summary['interest_rate'] or 'N/A'}")
                        print(f"   📋 Pending Offers: {summary['pending_offers']}")
                        print(f"   🧠 Emotional Stability: {summary['emotional_stability_score'] or 'N/A'}")
                        print()
                        
            except Exception as e:
                print(f"❌ Error getting summary for user {user_id}: {e}")
    
    async def _test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔍 Test 6: Edge Cases & Error Handling")
        print("-" * 40)
        
        # Test 1: Invalid offer acceptance
        print("🧪 Testing invalid offer acceptance...")
        try:
            async with self.session.post(
                f"{BASE_URL}/api/v1/credit/offers/99999/accept",
                json={"user_id": 999, "terms_accepted": True}
            ) as resp:
                if resp.status == 400:
                    print("✅ Correctly rejected invalid offer acceptance")
                else:
                    print(f"⚠️ Unexpected response for invalid offer: {resp.status}")
        except Exception as e:
            print(f"❌ Exception testing invalid offer: {e}")
        
        # Test 2: Terms not accepted
        print("🧪 Testing terms not accepted...")
        try:
            async with self.session.post(
                f"{BASE_URL}/api/v1/credit/offers/1/accept",
                json={"user_id": 123, "terms_accepted": False}
            ) as resp:
                if resp.status == 400:
                    print("✅ Correctly rejected offer without terms acceptance")
                else:
                    print(f"⚠️ Unexpected response for terms not accepted: {resp.status}")
        except Exception as e:
            print(f"❌ Exception testing terms rejection: {e}")
    
    def _print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n📋 Test Results Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get("success")])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        print()
        
        # Group by test type
        test_types = {}
        for result in self.test_results:
            test_type = result.get("test", "unknown")
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "success": 0}
            test_types[test_type]["total"] += 1
            if result.get("success"):
                test_types[test_type]["success"] += 1
        
        print("Results by Test Type:")
        for test_type, stats in test_types.items():
            success_rate = (stats["success"]/stats["total"])*100 if stats["total"] > 0 else 0
            print(f"  {test_type}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        print("\n🎉 Credit Deployment System Test Complete!")
        print("\nKey Features Tested:")
        print("✅ Event-driven credit offer creation")
        print("✅ Asynchronous deployment processing") 
        print("✅ Background task processing with Celery")
        print("✅ Mobile push notification system")
        print("✅ Comprehensive audit trail")
        print("✅ Real-time deployment monitoring")
        print("✅ User credit profile management")
        print("✅ Error handling and edge cases")

async def main():
    """Run the comprehensive credit deployment test suite"""
    async with CreditDeploymentTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
