#!/usr/bin/env python3
"""
Send test emotion events to verify source distribution fix
"""

import asyncio
import websockets
import json

async def send_test_emotions():
    """Send a few test emotion events"""
    token = "dev_ingest_token_please_change"
    user_id = 1
    session_id = f"test_session_{int(asyncio.get_event_loop().time())}"
    uri = f"ws://localhost:8000/ws/emotions/stream?user_id={user_id}&session_id={session_id}&token={token}"
    
    test_events = [
        {
            "user_id": 1,
            "emotion_label": "joy",
            "valence": 0.8,
            "arousal": 0.7,
            "source": "facial",
            "confidence": 0.9
        },
        {
            "user_id": 2,
            "emotion_label": "sadness",
            "valence": -0.6,
            "arousal": 0.4,
            "source": "voice",
            "confidence": 0.85
        },
        {
            "user_id": 3,
            "emotion_label": "anger",
            "valence": -0.7,
            "arousal": 0.9,
            "source": "text",
            "confidence": 0.8
        }
    ]
    
    try:
        print(f"Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to emotion stream!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            print(f"📩 Welcome message: {json.loads(welcome)}")
            
            # Send test events
            for i, event in enumerate(test_events):
                print(f"📤 Sending event {i+1}: {event['emotion_label']} from {event['source']}")
                await websocket.send(json.dumps(event))
                
                # Wait for response
                response = await websocket.recv()
                print(f"📥 Response: {json.loads(response)}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_emotions())
