#!/usr/bin/env python3
"""
Real-time Emotion Processing System Test Script

This script tests the comprehensive emotion processing capabilities including:
- WebSocket connection and communication
- Real-time emotion event processing
- Advanced analytics and pattern recognition
- Risk assessment and anomaly detection
"""

import asyncio
import json
import websockets
import time
from datetime import datetime
import random

async def test_emotion_stream():
    """Test the enhanced emotion stream endpoint"""
    print("🧠 Testing Real-time Emotion Stream")
    print("=" * 50)
    
    # Connection parameters
    user_id = 1
    token = "dev_ingest_token_please_change"  # Updated to use correct token
    url = f"ws://localhost:8000/ws/emotions/stream?user_id={user_id}&token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✅ Connected to emotion stream for user {user_id}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📩 Welcome message: {welcome_data['status']}")
            print(f"📊 Session ID: {welcome_data['session_id']}")
            
            # Test different emotion scenarios
            test_scenarios = [
                {
                    "name": "Positive Morning Energy",
                    "events": [
                        {"emotion_label": "joy", "valence": 0.8, "arousal": 0.7, "source": "facial"},
                        {"emotion_label": "optimism", "valence": 0.7, "arousal": 0.5, "source": "text"},
                        {"emotion_label": "excitement", "valence": 0.9, "arousal": 0.8, "source": "voice"}
                    ]
                },
                {
                    "name": "Stress Pattern",
                    "events": [
                        {"emotion_label": "anxiety", "valence": -0.3, "arousal": 0.8, "source": "physiological"},
                        {"emotion_label": "fear", "valence": -0.6, "arousal": 0.9, "source": "facial"},
                        {"emotion_label": "anger", "valence": -0.5, "arousal": 0.8, "source": "voice"}
                    ]
                },
                {
                    "name": "Recovery Journey",
                    "events": [
                        {"emotion_label": "sadness", "valence": -0.6, "arousal": 0.3, "source": "text"},
                        {"emotion_label": "neutral", "valence": 0.0, "arousal": 0.4, "source": "facial"},
                        {"emotion_label": "calm", "valence": 0.4, "arousal": 0.2, "source": "physiological"}
                    ]
                }
            ]
            
            for scenario in test_scenarios:
                print(f"\n🎭 Testing scenario: {scenario['name']}")
                print("-" * 30)
                
                for i, event_template in enumerate(scenario['events']):
                    # Create comprehensive emotion event
                    emotion_event = {
                        "user_id": user_id,
                        "source": event_template["source"],
                        "emotion_label": event_template["emotion_label"],
                        "valence": event_template["valence"],
                        "arousal": event_template["arousal"],
                        "confidence": round(random.uniform(0.7, 0.95), 2),
                        "timestamp": datetime.now().isoformat(),
                        "context": {
                            "time_period": "morning" if i == 0 else "afternoon",
                            "day_of_week": "thursday",
                            "scenario": scenario['name'].lower().replace(' ', '_')
                        },
                        "biometrics": {
                            "heart_rate": 70 + event_template["arousal"] * 30,
                            "skin_conductance": 5 + event_template["arousal"] * 5
                        } if event_template["source"] == "physiological" else None
                    }
                    
                    # Send emotion event
                    await websocket.send(json.dumps(emotion_event))
                    print(f"📤 Sent: {event_template['emotion_label']} "
                          f"(v:{event_template['valence']:.1f}, a:{event_template['arousal']:.1f})")
                    
                    # Receive response
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    print(f"📥 Response: {response_data['status']}")
                    
                    if 'analysis' in response_data:
                        analysis = response_data['analysis']
                        if analysis != "insufficient_data":
                            print(f"🔍 Analysis: {analysis.get('valence_trend', 'N/A')} valence, "
                                  f"{analysis.get('emotional_stability', 'N/A')} stability")
                    
                    if 'metrics' in response_data:
                        metrics = response_data['metrics']
                        print(f"📊 Session metrics: {metrics.get('event_count', 0)} events, "
                              f"avg valence: {metrics.get('avg_valence', 0):.2f}")
                    
                    await asyncio.sleep(1)  # Small delay between events
                
                await asyncio.sleep(2)  # Delay between scenarios
            
            print(f"\n✅ Completed emotion stream test for user {user_id}")
            
    except websockets.exceptions.ConnectionClosed:
        print("❌ Connection closed unexpectedly")
    except Exception as e:
        print(f"❌ Error testing emotion stream: {e}")

async def test_metrics_stream():
    """Test the real-time metrics endpoint"""
    print("\n📊 Testing Real-time Metrics Stream")
    print("=" * 50)
    
    token = "dev_ingest_token_please_change"  # Updated to use correct token
    url = f"ws://localhost:8000/ws/emotions/metrics?token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to metrics stream")
            
            # Receive a few metric updates
            for i in range(3):
                metrics = await websocket.recv()
                metrics_data = json.loads(metrics)
                
                print(f"📊 Metrics update {i+1}:")
                print(f"   Total events: {metrics_data['metrics']['total_events']}")
                print(f"   Events/min: {metrics_data['metrics']['events_per_minute']}")
                print(f"   Active users: {metrics_data['metrics']['unique_users']}")
                print(f"   Avg valence: {metrics_data['metrics']['avg_valence']:.2f}")
                print(f"   Dominant emotion: {metrics_data['metrics']['dominant_emotion']}")
                
                if i < 2:  # Don't wait after the last iteration
                    await asyncio.sleep(5)
            
            print("✅ Completed metrics stream test")
            
    except Exception as e:
        print(f"❌ Error testing metrics stream: {e}")

async def test_anomaly_detection():
    """Test anomaly detection with extreme emotion patterns"""
    print("\n🚨 Testing Anomaly Detection")
    print("=" * 50)
    
    user_id = 2
    token = "dev_ingest_token_please_change"
    url = f"ws://localhost:8000/ws/emotions/stream?user_id={user_id}&token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✅ Connected for anomaly testing (user {user_id})")
            
            # Receive welcome message
            await websocket.recv()
            
            # Send normal baseline events first
            print("📊 Establishing baseline...")
            for i in range(10):
                normal_event = {
                    "user_id": user_id,
                    "source": "facial",
                    "emotion_label": "neutral",
                    "valence": random.uniform(-0.1, 0.1),
                    "arousal": random.uniform(0.3, 0.5),
                    "confidence": 0.8,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(normal_event))
                await websocket.recv()  # Consume response
                await asyncio.sleep(0.5)
            
            # Send anomalous events
            print("⚠️ Sending anomalous patterns...")
            anomalous_events = [
                {"emotion_label": "anger", "valence": -0.9, "arousal": 0.95},  # Extreme negative high arousal
                {"emotion_label": "fear", "valence": -0.8, "arousal": 0.9},   # Another extreme
                {"emotion_label": "sadness", "valence": -0.9, "arousal": 0.1}, # Extreme low
            ]
            
            for event_data in anomalous_events:
                anomaly_event = {
                    "user_id": user_id,
                    "source": "physiological",
                    "emotion_label": event_data["emotion_label"],
                    "valence": event_data["valence"],
                    "arousal": event_data["arousal"],
                    "confidence": 0.9,
                    "timestamp": datetime.now().isoformat(),
                    "context": {"anomaly_test": True}
                }
                
                await websocket.send(json.dumps(anomaly_event))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"🚨 Sent anomaly: {event_data['emotion_label']} "
                      f"(v:{event_data['valence']:.1f}, a:{event_data['arousal']:.1f})")
                print(f"📥 Response status: {response_data['status']}")
                
                await asyncio.sleep(1)
            
            print("✅ Completed anomaly detection test")
            
    except Exception as e:
        print(f"❌ Error testing anomaly detection: {e}")

async def test_multi_source_integration():
    """Test integration of multiple emotion data sources"""
    print("\n🔗 Testing Multi-source Integration")
    print("=" * 50)
    
    user_id = 3
    token = "dev_ingest_token_please_change"
    url = f"ws://localhost:8000/ws/emotions/stream?user_id={user_id}&token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✅ Connected for multi-source testing (user {user_id})")
            
            # Receive welcome message
            await websocket.recv()
            
            # Test all supported sources
            sources_test = [
                {"source": "text", "emotion_label": "joy", "valence": 0.6, "arousal": 0.5},
                {"source": "voice", "emotion_label": "calm", "valence": 0.4, "arousal": 0.3},
                {"source": "facial", "emotion_label": "surprise", "valence": 0.1, "arousal": 0.8},
                {"source": "physiological", "emotion_label": "anxiety", "valence": -0.2, "arousal": 0.7},
                {"source": "survey", "emotion_label": "optimism", "valence": 0.7, "arousal": 0.6},
                {"source": "biometric", "emotion_label": "trust", "valence": 0.5, "arousal": 0.4},
                {"source": "behavioral", "emotion_label": "boredom", "valence": -0.2, "arousal": 0.1},
                {"source": "contextual", "emotion_label": "anticipation", "valence": 0.3, "arousal": 0.6}
            ]
            
            for source_test in sources_test:
                multi_source_event = {
                    "user_id": user_id,
                    "source": source_test["source"],
                    "emotion_label": source_test["emotion_label"],
                    "valence": source_test["valence"],
                    "arousal": source_test["arousal"],
                    "confidence": random.uniform(0.7, 0.95),
                    "timestamp": datetime.now().isoformat(),
                    "context": {
                        "source_test": True,
                        "integration_test": "multi_source"
                    }
                }
                
                # Add source-specific data
                if source_test["source"] == "physiological":
                    multi_source_event["biometrics"] = {
                        "heart_rate": 70 + source_test["arousal"] * 30,
                        "skin_conductance": 5 + source_test["arousal"] * 5
                    }
                elif source_test["source"] == "facial":
                    multi_source_event["raw_data"] = {
                        "face_landmarks": [[0.2, 0.3], [0.4, 0.5]],
                        "detection_quality": 0.95
                    }
                
                await websocket.send(json.dumps(multi_source_event))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"📡 Source: {source_test['source']} → {source_test['emotion_label']} "
                      f"({response_data['status']})")
                
                await asyncio.sleep(0.8)
            
            print("✅ Completed multi-source integration test")
            
    except Exception as e:
        print(f"❌ Error testing multi-source integration: {e}")

async def main():
    """Run comprehensive emotion processing tests"""
    print("🧠 CloudWalk Real-time Emotion Processing - System Test")
    print("=" * 70)
    print("Testing comprehensive emotion intelligence capabilities")
    print("=" * 70)
    
    # Check if server is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health') as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print("❌ Server health check failed")
                    return
    except:
        print("❌ Cannot connect to server. Please ensure the application is running.")
        print("   Run: docker-compose up -d")
        return
    
    # Run all tests
    tests = [
        test_emotion_stream,
        test_metrics_stream,
        test_anomaly_detection,
        test_multi_source_integration
    ]
    
    for test_func in tests:
        try:
            await test_func()
            await asyncio.sleep(2)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n🎉 All emotion processing tests completed!")
    print("\n📊 Next steps:")
    print("   1. Open emotion_dashboard.html to monitor real-time activity")
    print("   2. Run advanced_emotion_producer.py for stress testing")
    print("   3. Check database for stored emotional events")
    print("   4. Review REALTIME_EMOTION_PROCESSING.md for detailed documentation")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test suite error: {e}")
