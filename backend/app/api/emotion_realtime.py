"""
Enhanced Real-time Emotion Processing System

This module provides comprehensive real-time emotional data processing with:
- Multi-source emotion ingestion (text, voice, facial, physiological)
- Advanced emotion analysis and validation
- Real-time emotion state tracking
- Context-aware emotion interpretation
- Anomaly detection for emotional patterns
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Header, status, HTTPException
from pydantic import BaseModel, Field, validator
import numpy as np
from collections import defaultdict, deque

from app.config import settings
from app.tasks.emotion_ingest import persist_emotion_event, analyze_emotion_patterns
from app.services.emotion_analysis import EmotionAnalyzer, EmotionContext

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["real-time-emotions"])

class EmotionSource(str, Enum):
    """Supported emotion data sources"""
    TEXT = "text"
    VOICE = "voice" 
    FACIAL = "facial"
    PHYSIOLOGICAL = "physiological"
    SURVEY = "survey"
    BIOMETRIC = "biometric"
    BEHAVIORAL = "behavioral"
    CONTEXTUAL = "contextual"

class EmotionLabel(str, Enum):
    """Standard emotion labels based on Plutchik's emotion wheel"""
    # Primary emotions
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    TRUST = "trust"
    DISGUST = "disgust"
    SURPRISE = "surprise"
    ANTICIPATION = "anticipation"
    
    # Secondary emotions
    OPTIMISM = "optimism"
    DISAPPOINTMENT = "disappointment"
    CONTEMPT = "contempt"
    ANXIETY = "anxiety"
    LOVE = "love"
    REMORSE = "remorse"
    AWE = "awe"
    AGGRESSIVENESS = "aggressiveness"
    
    # Neutral/Unknown
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

@dataclass
class EmotionMetrics:
    """Real-time emotion metrics for monitoring"""
    total_events: int = 0
    events_per_minute: float = 0.0
    unique_users: int = 0
    unique_sessions: int = 0
    dominant_emotion: Optional[str] = None
    avg_valence: float = 0.0
    avg_arousal: float = 0.0
    source_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.source_distribution is None:
            self.source_distribution = {}

class EmotionEvent(BaseModel):
    """Enhanced emotion event model with validation"""
    user_id: int = Field(..., description="User identifier", gt=0)
    session_id: Optional[str] = Field(None, description="Session identifier")
    source: EmotionSource = Field(..., description="Data source type")
    
    # Core emotion data
    emotion_label: Optional[EmotionLabel] = Field(None, description="Detected emotion")
    valence: Optional[float] = Field(None, description="Emotion valence [-1.0 to 1.0]", ge=-1.0, le=1.0)
    arousal: Optional[float] = Field(None, description="Emotion arousal [0.0 to 1.0]", ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, description="Detection confidence [0.0 to 1.0]", ge=0.0, le=1.0)
    
    # Enhanced metadata
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    biometrics: Optional[Dict[str, float]] = Field(None, description="Biometric data (heart rate, etc.)")
    location: Optional[Dict[str, Any]] = Field(None, description="Location context")
    device_info: Optional[Dict[str, str]] = Field(None, description="Device information")
    
    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw sensor/input data")
    
    @validator('valence')
    def validate_valence(cls, v):
        if v is not None and not (-1.0 <= v <= 1.0):
            raise ValueError('Valence must be between -1.0 and 1.0')
        return v
    
    @validator('arousal', 'confidence')
    def validate_unit_interval(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Value must be between 0.0 and 1.0')
        return v

class ConnectionManager:
    """Manages WebSocket connections and real-time metrics"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[int, Set[str]] = defaultdict(set)
        self.session_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.metrics = EmotionMetrics()
        self.emotion_analyzer = EmotionAnalyzer()
        
        # Real-time monitoring
        self.recent_events = deque(maxlen=1000)
        self.start_time = datetime.now()
        
    async def connect(self, websocket: WebSocket, session_id: str, user_id: int):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[user_id].add(session_id)
        logger.info(f"New emotion connection: session={session_id}, user={user_id}")
        
    def disconnect(self, session_id: str, user_id: int):
        """Handle WebSocket disconnection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        self.user_sessions[user_id].discard(session_id)
        if not self.user_sessions[user_id]:
            del self.user_sessions[user_id]
        logger.info(f"Emotion connection closed: session={session_id}, user={user_id}")
        
    async def process_emotion_event(self, event: EmotionEvent, session_id: str) -> Dict[str, Any]:
        """Process incoming emotion event with analysis"""
        try:
            # Add to recent events for metrics
            self.recent_events.append({
                'timestamp': datetime.now(),
                'user_id': event.user_id,
                'session_id': session_id,
                'source': event.source.value if event.source else None,
                'emotion_label': event.emotion_label.value if event.emotion_label else None,
                'valence': event.valence,
                'arousal': event.arousal
            })
            
            # Store in session history
            self.session_events[session_id].append(event)
            
            # Analyze emotion patterns
            analysis_result = await self._analyze_emotion_context(event, session_id)
            
            # Prepare data for persistence - only include fields that exist in the model
            raw_payload = event.dict()
            # Convert datetime to string for JSON serialization
            if raw_payload.get('timestamp'):
                raw_payload['timestamp'] = raw_payload['timestamp'].isoformat()
                
            event_data = {
                "user_id": event.user_id,
                "session_id": session_id,
                "source": event.source.value,
                "emotion_label": event.emotion_label.value if event.emotion_label else None,
                "valence": event.valence,
                "arousal": event.arousal,
                "confidence": event.confidence,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "raw_payload": raw_payload
            }
            
            # Async persist to database
            task = persist_emotion_event.delay(event_data)
            
            # Trigger pattern analysis if enough data
            if len(self.session_events[session_id]) >= 5:
                analyze_emotion_patterns.delay(event.user_id, session_id)
            
            # Update real-time metrics
            self._update_metrics()
            
            return {
                "status": "processed",
                "task_id": task.id,
                "analysis": analysis_result,
                "metrics": self._get_session_metrics(session_id)
            }
            
        except Exception as e:
            logger.error(f"Error processing emotion event: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_emotion_context(self, event: EmotionEvent, session_id: str) -> Dict[str, Any]:
        """Analyze emotion in context of recent events"""
        recent_events = list(self.session_events[session_id])
        
        if len(recent_events) < 2:
            return {"analysis": "insufficient_data"}
        
        # Initialize default values
        valence_trend = "stable"
        arousal_trend = "stable"
        
        # Calculate emotion trajectory
        if len(recent_events) >= 3:
            recent_valences = [e.valence for e in recent_events[-3:] if e.valence is not None]
            recent_arousals = [e.arousal for e in recent_events[-3:] if e.arousal is not None]
            
            if len(recent_valences) >= 2:
                valence_change = recent_valences[-1] - recent_valences[0]
                if valence_change > 0.2:
                    valence_trend = "improving"
                elif valence_change < -0.2:
                    valence_trend = "declining"
            
            if len(recent_arousals) >= 2:
                arousal_change = recent_arousals[-1] - recent_arousals[0]
                if arousal_change > 0.2:
                    arousal_trend = "increasing"
                elif arousal_change < -0.2:
                    arousal_trend = "decreasing"
        
        # Detect patterns
        patterns = []
        emotion_labels = [e.emotion_label for e in recent_events[-5:] if e.emotion_label]
        
        if len(set(emotion_labels)) == 1 and len(emotion_labels) >= 3:
            patterns.append("consistent_emotion")
        
        if event.valence and event.valence < -0.5 and event.arousal and event.arousal > 0.7:
            patterns.append("high_stress")
        
        if event.valence and event.valence > 0.5 and event.arousal and event.arousal < 0.3:
            patterns.append("calm_positive")
        
        return {
            "analysis": "contextual",
            "valence_trend": valence_trend,
            "arousal_trend": arousal_trend,
            "patterns": patterns,
            "session_length": len(recent_events),
            "emotional_stability": self._calculate_stability(recent_events)
        }
    
    def _calculate_stability(self, events: List[EmotionEvent]) -> float:
        """Calculate emotional stability score"""
        if len(events) < 3:
            return 1.0
        
        valences = [e.valence for e in events if e.valence is not None]
        arousals = [e.arousal for e in events if e.arousal is not None]
        
        if not valences or not arousals:
            return 1.0
        
        valence_std = np.std(valences) if len(valences) > 1 else 0
        arousal_std = np.std(arousals) if len(arousals) > 1 else 0
        
        # Lower standard deviation = higher stability
        stability = 1.0 - min((valence_std + arousal_std) / 2, 1.0)
        return round(float(stability), 3)
    
    def _get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for specific session"""
        events = list(self.session_events[session_id])
        if not events:
            return {}
        
        valences = [e.valence for e in events if e.valence is not None]
        arousals = [e.arousal for e in events if e.arousal is not None]
        emotions = [e.emotion_label for e in events if e.emotion_label is not None]
        
        return {
            "event_count": len(events),
            "avg_valence": round(float(np.mean(valences)), 3) if valences else None,
            "avg_arousal": round(float(np.mean(arousals)), 3) if arousals else None,
            "dominant_emotion": max(set(emotions), key=emotions.count) if emotions else None,
            "stability_score": self._calculate_stability(events)
        }
    
    def _update_metrics(self):
        """Update global real-time metrics"""
        now = datetime.now()
        
        # Filter recent events (last minute)
        minute_ago = now - timedelta(minutes=1)
        recent = [e for e in self.recent_events if e['timestamp'] > minute_ago]
        
        self.metrics.total_events = len(self.recent_events)
        self.metrics.events_per_minute = len(recent)
        self.metrics.unique_users = len(set(e['user_id'] for e in recent))
        self.metrics.unique_sessions = len(set(e['session_id'] for e in recent))
        
        if recent:
            valences = [e['valence'] for e in recent if e['valence'] is not None]
            arousals = [e['arousal'] for e in recent if e['arousal'] is not None]
            emotions = [e['emotion_label'] for e in recent if e['emotion_label'] is not None]
            
            self.metrics.avg_valence = round(float(np.mean(valences)), 3) if valences else 0.0
            self.metrics.avg_arousal = round(float(np.mean(arousals)), 3) if arousals else 0.0
            self.metrics.dominant_emotion = max(set(emotions), key=emotions.count) if emotions else None
            
            # Source distribution - convert numpy types to Python types
            sources = [e['source'] for e in recent]
            if sources:
                unique_sources, counts = np.unique(sources, return_counts=True)
                self.metrics.source_distribution = {
                    str(source): int(count) for source, count in zip(unique_sources, counts)
                }
            else:
                self.metrics.source_distribution = {}

# Global connection manager
connection_manager = ConnectionManager()

def _auth_ok(token_qs: Optional[str], token_hdr: Optional[str]) -> bool:
    """Validate authentication token"""
    expected = getattr(settings, "ingest_token", None) or ""
    incoming = token_qs or token_hdr or ""
    return expected and (incoming == expected)

@router.websocket("/emotions/stream")
async def emotion_stream(
    websocket: WebSocket,
    user_id: int = Query(..., description="User ID for the emotion stream"),
    session_id: Optional[str] = Query(None, description="Session ID (auto-generated if not provided)"),
    token: Optional[str] = Query(None, description="Authentication token"),
    x_auth_token: Optional[str] = Header(None, description="Authentication token in header")
):
    """
    Enhanced WebSocket endpoint for real-time emotion data streaming
    
    Supports multiple data sources and provides real-time analysis
    """
    # Authentication check
    if not _auth_ok(token, x_auth_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Generate session ID if not provided
    if not session_id:
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
    
    try:
        await connection_manager.connect(websocket, session_id, user_id)
        
        # Send welcome message with session info
        welcome_msg = {
            "status": "connected",
            "session_id": session_id,
            "user_id": user_id,
            "supported_sources": [source.value for source in EmotionSource],
            "supported_emotions": [emotion.value for emotion in EmotionLabel],
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        while True:
            # Receive message
            message = await websocket.receive_text()
            
            try:
                # Parse JSON
                raw_data = json.loads(message)
                
                # Validate and create emotion event
                emotion_event = EmotionEvent(**raw_data)
                
                # Process the event
                result = await connection_manager.process_emotion_event(emotion_event, session_id)
                
                # Send response
                await websocket.send_text(json.dumps(result))
                
            except json.JSONDecodeError:
                error_response = {
                    "status": "error",
                    "error": "invalid_json",
                    "message": "Message must be valid JSON"
                }
                await websocket.send_text(json.dumps(error_response))
                
            except Exception as e:
                error_response = {
                    "status": "error", 
                    "error": "validation_error",
                    "message": str(e)
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id, user_id)
    except Exception as e:
        logger.error(f"Unexpected error in emotion stream: {e}")
        connection_manager.disconnect(session_id, user_id)

@router.websocket("/emotions/metrics")
async def emotion_metrics_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    x_auth_token: Optional[str] = Header(None)
):
    """
    Real-time emotion processing metrics stream for monitoring
    """
    if not _auth_ok(token, x_auth_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
    
    try:
        while True:
            # Send current metrics every 5 seconds
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(connection_manager.metrics),
                "active_connections": len(connection_manager.active_connections),
                "active_users": len(connection_manager.user_sessions)
            }
            
            await websocket.send_text(json.dumps(metrics_data))
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass

# Legacy endpoint for backward compatibility
@router.websocket("/emotions")
async def emotions_ws_legacy(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
    x_auth_token: Optional[str] = Header(default=None)
):
    """Legacy emotion WebSocket endpoint - redirects to enhanced stream"""
    if not _auth_ok(token, x_auth_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"status": "error", "error": "invalid_json"}))
                continue

            # Extract user_id (required)
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.send_text(json.dumps({"status": "error", "error": "missing user_id"}))
                continue

            # Build event for legacy format
            event = {
                "user_id": user_id,
                "session_id": payload.get("session_id"),
                "source": payload.get("source", "unknown"),
                "emotion_label": payload.get("emotion_label"),
                "valence": payload.get("valence"),
                "arousal": payload.get("arousal"),
                "confidence": payload.get("confidence"),
                "timestamp": payload.get("timestamp"),
                "raw_payload": payload,
            }

            # Hand off to Celery (original behavior)
            task = persist_emotion_event.delay(event)
            await websocket.send_text(json.dumps({"status": "queued", "task_id": task.id}))
            
    except WebSocketDisconnect:
        pass
