# mock_http_producer.py
import requests
import json
import random
from datetime import datetime
import time

def send_emotion_events():
    # Note: This would require creating an HTTP endpoint
    # For now, this is a template if you want to add HTTP endpoints
    url = "http://localhost:8000/emotions/ingest"  # Hypothetical endpoint
    emotions = ["joy", "calm", "surprise", "anger", "sadness"]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dev_ingest_token_please_change"
    }
    
    for i in range(5):
        event = {
            "user_id": 1,
            "session_id": f"session_{i}",
            "source": random.choice(["text", "voice", "face"]),
            "emotion_label": random.choice(emotions),
            "valence": round(random.uniform(0, 1), 2),
            "arousal": round(random.uniform(0, 1), 2),
            "confidence": round(random.uniform(0.7, 1), 2),
            "raw_payload": {"source": "mock_http", "batch": i}
        }
        
        try:
            response = requests.post(url, json=event, headers=headers)
            print(f"Sent: {event}")
            print(f"Response: {response.status_code} - {response.text}")
            print("-" * 50)
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    send_emotion_events()
