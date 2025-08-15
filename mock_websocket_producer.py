# mock_websocket_producer.py
import asyncio
import websockets
import json
import random
from datetime import datetime

async def send_emotion_events():
    uri = "ws://localhost:8000/ws/emotions?token=dev_ingest_token_please_change"
    emotions = ["joy", "calm", "surprise", "anger", "sadness"]
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket!")
            
            for i in range(5):
                event = {
                    "user_id": 1,
                    "session_id": f"session_{i}",
                    "source": random.choice(["text", "voice", "face"]),
                    "emotion_label": random.choice(emotions),
                    "valence": round(random.uniform(0, 1), 2),
                    "arousal": round(random.uniform(0, 1), 2),
                    "confidence": round(random.uniform(0.7, 1), 2),
                    "raw_payload": {"source": "mock_producer", "batch": i}
                }
                
                await websocket.send(json.dumps(event))
                response = await websocket.recv()
                print(f"Sent: {event}")
                print(f"Response: {response}")
                print("-" * 50)
                
                # Wait a bit between messages
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_emotion_events())
