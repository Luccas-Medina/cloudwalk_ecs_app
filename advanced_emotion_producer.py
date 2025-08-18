"""
Advanced Emotion Data Producer for Real-time Testing

This script simulates various emotion data sources sending real-time emotional data
to test the comprehensive emotion processing system.
"""

import asyncio
import json
import random
import websockets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class EmotionProfile:
    """User emotion profile for realistic simulation"""
    user_id: int
    baseline_valence: float  # User's typical emotional baseline
    baseline_arousal: float
    volatility: float  # How much emotions vary
    stress_level: float  # Current stress level
    personality_type: str  # "stable", "volatile", "optimistic", "pessimistic"

class EmotionDataGenerator:
    """Generates realistic emotion data based on various scenarios"""
    
    def __init__(self):
        self.emotion_labels = [
            "joy", "sadness", "anger", "fear", "trust", "disgust", 
            "surprise", "anticipation", "optimism", "disappointment",
            "anxiety", "calm", "excitement", "boredom", "neutral"
        ]
        
        self.sources = [
            "text", "voice", "facial", "physiological", 
            "survey", "biometric", "behavioral", "contextual"
        ]
        
        # Emotion to valence/arousal mappings (approximate)
        self.emotion_mappings = {
            "joy": (0.7, 0.6),
            "sadness": (-0.6, 0.3),
            "anger": (-0.5, 0.8),
            "fear": (-0.7, 0.8),
            "trust": (0.5, 0.4),
            "disgust": (-0.6, 0.5),
            "surprise": (0.1, 0.8),
            "anticipation": (0.3, 0.6),
            "optimism": (0.8, 0.5),
            "disappointment": (-0.4, 0.4),
            "anxiety": (-0.3, 0.7),
            "calm": (0.4, 0.2),
            "excitement": (0.8, 0.9),
            "boredom": (-0.2, 0.1),
            "neutral": (0.0, 0.3)
        }
        
    def generate_realistic_emotion(self, profile: EmotionProfile, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate realistic emotion data based on user profile"""
        
        # Base emotion on profile and add some randomness
        valence = profile.baseline_valence + random.gauss(0, profile.volatility)
        arousal = profile.baseline_arousal + random.gauss(0, profile.volatility * 0.7)
        
        # Apply stress influence
        if profile.stress_level > 0.5:
            valence -= profile.stress_level * 0.3
            arousal += profile.stress_level * 0.4
        
        # Clamp values
        valence = max(-1.0, min(1.0, valence))
        arousal = max(0.0, min(1.0, arousal))
        
        # Select emotion label based on valence/arousal
        emotion_label = self._select_emotion_label(valence, arousal)
        
        # Generate confidence based on source reliability
        source = random.choice(self.sources)
        confidence = self._get_source_confidence(source)
        
        # Create emotion event
        emotion_event = {
            "user_id": profile.user_id,
            "session_id": f"session_{profile.user_id}_{int(time.time() // 300)}",  # 5-minute sessions
            "source": source,
            "emotion_label": emotion_label,
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "confidence": round(confidence, 3),
            "timestamp": datetime.now().isoformat(),
            "context": self._generate_context(source, context),
            "biometrics": self._generate_biometrics(arousal) if source in ["physiological", "biometric"] else None,
            "location": self._generate_location() if random.random() < 0.3 else None,
            "device_info": self._generate_device_info() if random.random() < 0.2 else None,
            "raw_data": self._generate_raw_data(source, emotion_label)
        }
        
        return emotion_event
    
    def _select_emotion_label(self, valence: float, arousal: float) -> str:
        """Select appropriate emotion label based on valence/arousal"""
        
        # Find closest emotion based on valence/arousal
        min_distance = float('inf')
        closest_emotion = "neutral"
        
        for emotion, (em_val, em_ar) in self.emotion_mappings.items():
            distance = np.sqrt((valence - em_val)**2 + (arousal - em_ar)**2)
            if distance < min_distance:
                min_distance = distance
                closest_emotion = emotion
        
        # Add some randomness
        if random.random() < 0.1:  # 10% chance of different emotion
            return random.choice(self.emotion_labels)
        
        return closest_emotion
    
    def _get_source_confidence(self, source: str) -> float:
        """Get confidence level based on data source reliability"""
        confidence_ranges = {
            "text": (0.6, 0.8),
            "voice": (0.7, 0.9),
            "facial": (0.8, 0.95),
            "physiological": (0.85, 0.98),
            "survey": (0.9, 0.99),
            "biometric": (0.9, 0.99),
            "behavioral": (0.5, 0.7),
            "contextual": (0.4, 0.6)
        }
        
        range_min, range_max = confidence_ranges.get(source, (0.5, 0.8))
        return random.uniform(range_min, range_max)
    
    def _generate_context(self, source: str, external_context: Dict = None) -> Dict[str, Any]:
        """Generate contextual information"""
        context = {}
        
        if external_context:
            context.update(external_context)
        
        # Source-specific context
        if source == "text":
            context.update({
                "message_type": random.choice(["chat", "email", "social_media", "sms"]),
                "message_length": random.randint(10, 500),
                "contains_emojis": random.choice([True, False])
            })
        elif source == "voice":
            context.update({
                "call_type": random.choice(["phone", "video", "voice_message"]),
                "speech_rate": round(random.uniform(80, 200), 1),  # words per minute
                "volume_level": round(random.uniform(0.3, 1.0), 2)
            })
        elif source == "facial":
            context.update({
                "detection_quality": round(random.uniform(0.7, 1.0), 2),
                "lighting_conditions": random.choice(["good", "moderate", "poor"]),
                "face_angle": random.choice(["frontal", "profile", "three_quarter"])
            })
        elif source in ["physiological", "biometric"]:
            context.update({
                "sensor_type": random.choice(["heart_rate", "skin_conductance", "breathing", "temperature"]),
                "measurement_duration": random.randint(30, 300)  # seconds
            })
        
        # General context
        hour = datetime.now().hour
        if 6 <= hour < 12:
            time_period = "morning"
        elif 12 <= hour < 18:
            time_period = "afternoon"
        elif 18 <= hour < 22:
            time_period = "evening"
        else:
            time_period = "night"
        
        context.update({
            "time_period": time_period,
            "day_of_week": datetime.now().strftime("%A").lower(),
            "weather": random.choice(["sunny", "cloudy", "rainy", "stormy", "clear"])
        })
        
        return context
    
    def _generate_biometrics(self, arousal: float) -> Dict[str, float]:
        """Generate realistic biometric data based on arousal level"""
        base_hr = 70
        hr_variation = arousal * 40  # High arousal increases heart rate
        
        return {
            "heart_rate": round(base_hr + hr_variation + random.gauss(0, 5), 1),
            "skin_conductance": round(arousal * 10 + random.gauss(0, 1), 2),
            "breathing_rate": round(16 + arousal * 8 + random.gauss(0, 2), 1),
            "temperature": round(98.6 + random.gauss(0, 0.5), 1)
        }
    
    def _generate_location(self) -> Dict[str, Any]:
        """Generate location context"""
        locations = ["home", "office", "car", "restaurant", "gym", "park", "store"]
        return {
            "type": random.choice(locations),
            "latitude": round(random.uniform(-90, 90), 6),
            "longitude": round(random.uniform(-180, 180), 6),
            "accuracy": round(random.uniform(5, 50), 1)
        }
    
    def _generate_device_info(self) -> Dict[str, str]:
        """Generate device information"""
        devices = ["smartphone", "tablet", "laptop", "desktop", "smartwatch", "fitness_tracker"]
        platforms = ["iOS", "Android", "Windows", "macOS", "Linux"]
        
        return {
            "device_type": random.choice(devices),
            "platform": random.choice(platforms),
            "app_version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        }
    
    def _generate_raw_data(self, source: str, emotion_label: str) -> Dict[str, Any]:
        """Generate raw sensor/input data"""
        if source == "text":
            return {
                "text_sample": f"Sample text showing {emotion_label} emotion...",
                "word_count": random.randint(5, 100),
                "sentiment_scores": {
                    "positive": random.uniform(0, 1),
                    "negative": random.uniform(0, 1),
                    "neutral": random.uniform(0, 1)
                }
            }
        elif source == "voice":
            return {
                "audio_duration": random.uniform(1, 30),
                "frequency_analysis": {
                    "fundamental_freq": random.uniform(80, 300),
                    "formants": [random.uniform(500, 3000) for _ in range(3)]
                },
                "speech_features": {
                    "jitter": random.uniform(0, 0.05),
                    "shimmer": random.uniform(0, 0.1)
                }
            }
        elif source == "facial":
            return {
                "face_landmarks": [[random.uniform(0, 1), random.uniform(0, 1)] for _ in range(68)],
                "action_units": {f"AU{i}": random.uniform(0, 5) for i in range(1, 26)},
                "head_pose": {
                    "pitch": random.uniform(-30, 30),
                    "yaw": random.uniform(-45, 45),
                    "roll": random.uniform(-15, 15)
                }
            }
        else:
            return {"sensor_reading": random.uniform(0, 100)}

class EmotionDataProducer:
    """Advanced emotion data producer for testing"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/emotions/stream"):
        self.websocket_url = websocket_url
        self.generator = EmotionDataGenerator()
        self.user_profiles = self._create_user_profiles()
        self.active_sessions = {}
        
    def _create_user_profiles(self) -> List[EmotionProfile]:
        """Create diverse user profiles for testing"""
        profiles = []
        
        # Stable users
        for i in range(1, 4):
            profiles.append(EmotionProfile(
                user_id=i,
                baseline_valence=random.uniform(0.2, 0.6),
                baseline_arousal=random.uniform(0.3, 0.5),
                volatility=random.uniform(0.1, 0.2),
                stress_level=random.uniform(0.1, 0.3),
                personality_type="stable"
            ))
        
        # Volatile users
        for i in range(4, 7):
            profiles.append(EmotionProfile(
                user_id=i,
                baseline_valence=random.uniform(-0.2, 0.4),
                baseline_arousal=random.uniform(0.4, 0.7),
                volatility=random.uniform(0.3, 0.5),
                stress_level=random.uniform(0.3, 0.6),
                personality_type="volatile"
            ))
        
        # High-stress users (for risk detection testing)
        for i in range(7, 9):
            profiles.append(EmotionProfile(
                user_id=i,
                baseline_valence=random.uniform(-0.6, -0.2),
                baseline_arousal=random.uniform(0.6, 0.8),
                volatility=random.uniform(0.2, 0.4),
                stress_level=random.uniform(0.7, 0.9),
                personality_type="high_stress"
            ))
        
        # Optimistic users
        for i in range(9, 11):
            profiles.append(EmotionProfile(
                user_id=i,
                baseline_valence=random.uniform(0.5, 0.8),
                baseline_arousal=random.uniform(0.3, 0.6),
                volatility=random.uniform(0.1, 0.3),
                stress_level=random.uniform(0.1, 0.2),
                personality_type="optimistic"
            ))
        
        return profiles
    
    async def simulate_single_user_stream(self, profile: EmotionProfile, duration_minutes: int = 5):
        """Simulate emotion stream for a single user"""
        auth_token = "your_test_token_here"  # Replace with actual token
        url = f"{self.websocket_url}?user_id={profile.user_id}&token={auth_token}"
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"Connected emotion stream for user {profile.user_id} ({profile.personality_type})")
                
                # Receive welcome message
                welcome = await websocket.recv()
                print(f"User {profile.user_id} welcome: {welcome}")
                
                end_time = time.time() + (duration_minutes * 60)
                event_count = 0
                
                while time.time() < end_time:
                    # Generate emotion event
                    emotion_event = self.generator.generate_realistic_emotion(profile)
                    
                    # Send to WebSocket
                    await websocket.send(json.dumps(emotion_event))
                    
                    # Receive response
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    event_count += 1
                    
                    if event_count % 10 == 0:
                        print(f"User {profile.user_id}: Sent {event_count} events, last response: {response_data.get('status')}")
                    
                    # Wait before next event (simulate realistic timing)
                    await asyncio.sleep(random.uniform(2, 10))
                
                print(f"Completed emotion stream for user {profile.user_id}: {event_count} events sent")
                
        except Exception as e:
            print(f"Error in emotion stream for user {profile.user_id}: {e}")
    
    async def simulate_multiple_users(self, num_users: int = 5, duration_minutes: int = 10):
        """Simulate multiple users sending emotion data simultaneously"""
        profiles_to_use = self.user_profiles[:num_users]
        
        print(f"Starting emotion simulation for {num_users} users for {duration_minutes} minutes")
        
        # Start all user streams concurrently
        tasks = [
            self.simulate_single_user_stream(profile, duration_minutes)
            for profile in profiles_to_use
        ]
        
        await asyncio.gather(*tasks)
        print("All user emotion simulations completed")
    
    async def test_emotion_scenarios(self):
        """Test specific emotion scenarios"""
        print("Testing specific emotion scenarios...")
        
        # Test high-stress scenario
        stress_profile = EmotionProfile(
            user_id=999,
            baseline_valence=-0.7,
            baseline_arousal=0.8,
            volatility=0.5,
            stress_level=0.9,
            personality_type="crisis"
        )
        
        # Test emotional recovery scenario
        recovery_profile = EmotionProfile(
            user_id=998,
            baseline_valence=0.1,  # Starting neutral
            baseline_arousal=0.5,
            volatility=0.2,
            stress_level=0.3,
            personality_type="recovering"
        )
        
        # Simulate gradually improving emotions for recovery profile
        await self.simulate_emotional_journey(recovery_profile, "recovery")
        
        # Simulate crisis scenario
        await self.simulate_emotional_journey(stress_profile, "crisis")
    
    async def simulate_emotional_journey(self, profile: EmotionProfile, journey_type: str):
        """Simulate a specific emotional journey"""
        auth_token = "your_test_token_here"
        url = f"{self.websocket_url}?user_id={profile.user_id}&token={auth_token}"
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"Starting {journey_type} journey for user {profile.user_id}")
                
                welcome = await websocket.recv()
                
                # Simulate journey over 20 events
                for i in range(20):
                    if journey_type == "recovery":
                        # Gradually improve emotions
                        progress = i / 19  # 0 to 1
                        profile.baseline_valence = -0.3 + (progress * 0.8)  # -0.3 to 0.5
                        profile.stress_level = 0.6 - (progress * 0.4)  # 0.6 to 0.2
                    elif journey_type == "crisis":
                        # Simulate emotional crisis
                        if i < 10:
                            profile.baseline_valence -= 0.05  # Getting worse
                            profile.stress_level += 0.03
                        else:
                            profile.baseline_valence += 0.02  # Slight recovery
                    
                    emotion_event = self.generator.generate_realistic_emotion(profile)
                    await websocket.send(json.dumps(emotion_event))
                    
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    print(f"{journey_type} event {i+1}: valence={emotion_event['valence']:.2f}, "
                          f"response={response_data.get('status')}")
                    
                    await asyncio.sleep(1)
                
                print(f"Completed {journey_type} journey for user {profile.user_id}")
                
        except Exception as e:
            print(f"Error in {journey_type} journey: {e}")

async def main():
    """Main function to run emotion data simulation"""
    producer = EmotionDataProducer()
    
    print("CloudWalk Emotion Processing System - Advanced Testing")
    print("=" * 60)
    
    # Test options
    test_scenarios = {
        "1": ("Single user stream", lambda: producer.simulate_single_user_stream(producer.user_profiles[0], 3)),
        "2": ("Multiple users (5 min)", lambda: producer.simulate_multiple_users(5, 5)),
        "3": ("Emotion scenarios", lambda: producer.test_emotion_scenarios()),
        "4": ("Stress test (10 users)", lambda: producer.simulate_multiple_users(10, 10)),
        "5": ("All scenarios", lambda: run_all_scenarios(producer))
    }
    
    print("\nAvailable test scenarios:")
    for key, (description, _) in test_scenarios.items():
        print(f"{key}. {description}")
    
    choice = input("\nSelect test scenario (1-5): ").strip()
    
    if choice in test_scenarios:
        description, test_func = test_scenarios[choice]
        print(f"\nRunning: {description}")
        await test_func()
    else:
        print("Invalid choice. Running single user stream...")
        await producer.simulate_single_user_stream(producer.user_profiles[0], 3)

async def run_all_scenarios(producer):
    """Run all test scenarios sequentially"""
    print("Running all emotion testing scenarios...")
    
    # Quick single user test
    await producer.simulate_single_user_stream(producer.user_profiles[0], 2)
    await asyncio.sleep(2)
    
    # Multiple users test
    await producer.simulate_multiple_users(3, 3)
    await asyncio.sleep(2)
    
    # Emotion scenarios
    await producer.test_emotion_scenarios()
    
    print("All scenarios completed!")

if __name__ == "__main__":
    asyncio.run(main())
