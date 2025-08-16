#!/usr/bin/env python3
"""
Test script to check the metrics WebSocket endpoint
"""

import asyncio
import websockets
import json

async def test_metrics_websocket():
    """Test the metrics WebSocket endpoint"""
    token = "dev_ingest_token_please_change"
    uri = f"ws://localhost:8000/ws/emotions/metrics?token={token}"
    
    try:
        print(f"Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to metrics WebSocket!")
            print("📢 Now go to http://localhost:8000/dashboard, click 'Connect to Metrics', then 'Start Simulation'")
            
            # Wait for messages for 60 seconds to capture simulation data
            try:
                for i in range(12):  # Listen for 12 messages over 60 seconds
                    print(f"\n🔄 Waiting for message {i+1}...")
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    print(f"📊 Received metrics:")
                    print(f"  Timestamp: {data.get('timestamp')}")
                    print(f"  Active connections: {data.get('active_connections')}")
                    print(f"  Active users: {data.get('active_users')}")
                    
                    metrics = data.get('metrics', {})
                    print(f"  Total events: {metrics.get('total_events')}")
                    print(f"  Events per minute: {metrics.get('events_per_minute')}")
                    print(f"  Unique users: {metrics.get('unique_users')}")
                    print(f"  Avg valence: {metrics.get('avg_valence')}")
                    print(f"  Avg arousal: {metrics.get('avg_arousal')}")
                    print(f"  Dominant emotion: {metrics.get('dominant_emotion')}")
                    print(f"  Source distribution: {metrics.get('source_distribution')}")
                    
            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for messages")
                
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(test_metrics_websocket())
