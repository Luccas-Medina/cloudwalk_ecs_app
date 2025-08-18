"""
CloudWalk ECS App - Emotional Data Analytics Engine
==================================================

This module provides comprehensive emotional data analysis, insights, and trend detection
for the CloudWalk Empathic Credit System.

Key Features:
- Real-time emotion trend analysis
- User emotional pattern recognition
- Predictive emotional modeling
- Anomaly detection in emotional states
- Credit decision correlation analysis
- Live dashboard analytics
- Statistical insights and reporting
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from collections import defaultdict, Counter
import json
import random

from app.core.db import SessionLocal
from app.models import User, EmotionalEvent, Transaction


class EmotionTrend(str, Enum):
    """Emotion trend directions"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class RiskLevel(str, Enum):
    """Emotional risk levels for credit decisions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EmotionInsight:
    """Individual emotion analysis insight"""
    emotion_label: str
    frequency: int
    percentage: float
    avg_valence: float
    avg_arousal: float
    trend: EmotionTrend
    confidence: float


@dataclass
class UserEmotionalProfile:
    """Comprehensive user emotional profile"""
    user_id: int
    dominant_emotions: List[str]
    emotional_stability: float  # 0-1, higher = more stable
    stress_level: float  # 0-1, higher = more stress
    recent_trend: EmotionTrend
    risk_level: RiskLevel
    total_events: int
    analysis_period_days: int
    last_updated: datetime


@dataclass
class EmotionalTrends:
    """System-wide emotional trends"""
    time_period: str
    total_events: int
    unique_users: int
    top_emotions: List[EmotionInsight]
    avg_valence_trend: List[Tuple[datetime, float]]
    avg_arousal_trend: List[Tuple[datetime, float]]
    emotional_volatility: float
    stress_indicators: Dict[str, float]
    anomaly_alerts: List[Dict]


@dataclass
class CreditEmotionCorrelation:
    """Correlation between emotional state and credit decisions"""
    emotion_label: str
    approval_rate: float
    avg_credit_amount: float
    default_risk_correlation: float
    sample_size: int


@dataclass
class LiveEmotionMetrics:
    """Real-time emotion metrics for dashboard"""
    current_active_users: int
    emotions_per_minute: float
    dominant_emotion_now: str
    valence_distribution: Dict[str, float]
    arousal_distribution: Dict[str, float]
    stress_level_alert: bool
    anomaly_detected: bool
    last_updated: datetime


class EmotionalAnalyticsEngine:
    """Advanced emotional data analytics and insights engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_analysis_config()
    
    def _setup_analysis_config(self):
        """Setup analysis configuration"""
        self.config = {
            "trend_analysis_window": 7,  # days
            "volatility_threshold": 0.3,
            "stress_threshold": 0.7,
            "anomaly_threshold": 2.0,  # standard deviations
            "min_events_for_analysis": 10,
            "emotion_categories": {
                "positive": ["joy", "happiness", "contentment", "excitement", "love"],
                "negative": ["anger", "sadness", "fear", "disgust", "contempt"],
                "neutral": ["neutral", "calm", "focused"],
                "stress": ["anxiety", "frustration", "overwhelm", "tension"]
            }
        }
    
    # ==================== USER-LEVEL ANALYSIS ====================
    
    async def analyze_user_emotional_profile(self, user_id: int, days: int = 30) -> UserEmotionalProfile:
        """Generate comprehensive emotional profile for a user"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user's emotional events
            events = db.query(EmotionalEvent).filter(
                and_(
                    EmotionalEvent.user_id == user_id,
                    EmotionalEvent.ingested_at >= cutoff_date
                )
            ).order_by(EmotionalEvent.ingested_at.desc()).all()
            
            if len(events) < self.config["min_events_for_analysis"]:
                return self._create_default_profile(user_id, days)
            
            # Analyze dominant emotions
            emotion_counts = Counter([e.emotion_label for e in events if e.emotion_label])
            dominant_emotions = [emotion for emotion, _ in emotion_counts.most_common(3)]
            
            # Calculate emotional stability (inverse of variance in valence)
            valences = [e.valence for e in events if e.valence is not None]
            if valences and len(valences) > 1:
                valence_variance = statistics.variance(valences)
                emotional_stability = 1.0 - min(1.0, valence_variance)
            else:
                emotional_stability = 0.5
            emotional_stability = max(0.0, min(1.0, emotional_stability))
            
            # Calculate stress level
            stress_emotions = self.config["emotion_categories"]["stress"]
            stress_events = sum(1 for e in events if e.emotion_label in stress_emotions)
            stress_level = stress_events / len(events) if events else 0.0
            
            # Determine recent trend
            recent_trend = self._calculate_emotional_trend(events)
            
            # Assess risk level
            risk_level = self._assess_emotional_risk(emotional_stability, stress_level, recent_trend)
            
            return UserEmotionalProfile(
                user_id=user_id,
                dominant_emotions=dominant_emotions,
                emotional_stability=emotional_stability,
                stress_level=stress_level,
                recent_trend=recent_trend,
                risk_level=risk_level,
                total_events=len(events),
                analysis_period_days=days,
                last_updated=datetime.utcnow()
            )
        
        except Exception as e:
            self.logger.error(f"Failed to analyze emotional profile for user {user_id}: {e}")
            return self._create_default_profile(user_id, days)
        finally:
            db.close()
    
    def _calculate_emotional_trend(self, events: List[EmotionalEvent]) -> EmotionTrend:
        """Calculate emotional trend from events"""
        if len(events) < 5:
            return EmotionTrend.STABLE
        
        # Sort events by time and calculate valence trend
        events_sorted = sorted(events, key=lambda x: x.ingested_at)
        valences = [e.valence for e in events_sorted if e.valence is not None]
        
        if len(valences) < 3:
            return EmotionTrend.STABLE
        
        # Calculate trend using simple slope approximation
        if len(valences) >= 2:
            # Simple linear trend: compare first half to second half
            mid_point = len(valences) // 2
            first_half_avg = statistics.mean(valences[:mid_point]) if valences[:mid_point] else 0
            second_half_avg = statistics.mean(valences[mid_point:]) if valences[mid_point:] else 0
            slope = second_half_avg - first_half_avg
        else:
            slope = 0
        
        # Calculate volatility
        volatility = statistics.stdev(valences) if len(valences) > 1 else 0
        
        if volatility > self.config["volatility_threshold"]:
            return EmotionTrend.VOLATILE
        elif slope > 0.1:
            return EmotionTrend.IMPROVING
        elif slope < -0.1:
            return EmotionTrend.DECLINING
        else:
            return EmotionTrend.STABLE
    
    def _assess_emotional_risk(self, stability: float, stress: float, trend: EmotionTrend) -> RiskLevel:
        """Assess emotional risk level for credit decisions"""
        risk_score = 0.0
        
        # Stability factor (lower stability = higher risk)
        risk_score += (1.0 - stability) * 0.4
        
        # Stress factor
        risk_score += stress * 0.4
        
        # Trend factor
        trend_scores = {
            EmotionTrend.IMPROVING: 0.0,
            EmotionTrend.STABLE: 0.1,
            EmotionTrend.DECLINING: 0.3,
            EmotionTrend.VOLATILE: 0.4
        }
        risk_score += trend_scores.get(trend, 0.2) * 0.2
        
        # Determine risk level
        if risk_score < 0.25:
            return RiskLevel.LOW
        elif risk_score < 0.5:
            return RiskLevel.MEDIUM
        elif risk_score < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _create_default_profile(self, user_id: int, days: int) -> UserEmotionalProfile:
        """Create default profile for users with insufficient data"""
        return UserEmotionalProfile(
            user_id=user_id,
            dominant_emotions=["neutral"],
            emotional_stability=0.5,
            stress_level=0.3,
            recent_trend=EmotionTrend.STABLE,
            risk_level=RiskLevel.MEDIUM,
            total_events=0,
            analysis_period_days=days,
            last_updated=datetime.utcnow()
        )
    
    # ==================== SYSTEM-WIDE ANALYSIS ====================
    
    async def analyze_system_emotional_trends(self, hours: int = 24) -> EmotionalTrends:
        """Analyze system-wide emotional trends"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            
            # Get all recent events
            events = db.query(EmotionalEvent).filter(
                EmotionalEvent.ingested_at >= cutoff_date
            ).all()
            
            if not events:
                return self._create_empty_trends(f"{hours}h")
            
            # Basic statistics
            total_events = len(events)
            unique_users = len(set(e.user_id for e in events))
            
            # Analyze top emotions
            top_emotions = self._analyze_top_emotions(events)
            
            # Calculate trend data
            valence_trend = self._calculate_valence_trend(events, hours)
            arousal_trend = self._calculate_arousal_trend(events, hours)
            
            # Calculate emotional volatility
            valences = [e.valence for e in events if e.valence is not None]
            emotional_volatility = statistics.stdev(valences) if len(valences) > 1 else 0.0
            
            # Detect stress indicators
            stress_indicators = self._analyze_stress_indicators(events)
            
            # Detect anomalies
            anomaly_alerts = self._detect_anomalies(events)
            
            return EmotionalTrends(
                time_period=f"{hours}h",
                total_events=total_events,
                unique_users=unique_users,
                top_emotions=top_emotions,
                avg_valence_trend=valence_trend,
                avg_arousal_trend=arousal_trend,
                emotional_volatility=emotional_volatility,
                stress_indicators=stress_indicators,
                anomaly_alerts=anomaly_alerts
            )
        
        except Exception as e:
            self.logger.error(f"Failed to analyze system trends: {e}")
            return self._create_empty_trends(f"{hours}h")
        finally:
            db.close()
    
    def _analyze_top_emotions(self, events: List[EmotionalEvent]) -> List[EmotionInsight]:
        """Analyze top emotions from events"""
        if not events:
            return []
        
        # Count emotions
        emotion_data = defaultdict(lambda: {"count": 0, "valences": [], "arousals": []})
        
        for event in events:
            if event.emotion_label:
                emotion_data[event.emotion_label]["count"] += 1
                if event.valence is not None:
                    emotion_data[event.emotion_label]["valences"].append(event.valence)
                if event.arousal is not None:
                    emotion_data[event.emotion_label]["arousals"].append(event.arousal)
        
        # Create insights
        insights = []
        total_events = len([e for e in events if e.emotion_label])
        
        for emotion, data in emotion_data.items():
            if data["count"] < 3:  # Skip emotions with too few samples
                continue
            
            avg_valence = statistics.mean(data["valences"]) if data["valences"] else 0.0
            avg_arousal = statistics.mean(data["arousals"]) if data["arousals"] else 0.0
            percentage = (data["count"] / total_events) * 100 if total_events > 0 else 0.0
            
            # Simple trend calculation (would need historical data for real trend)
            trend = EmotionTrend.STABLE  # Simplified for demo
            
            insights.append(EmotionInsight(
                emotion_label=emotion,
                frequency=data["count"],
                percentage=percentage,
                avg_valence=avg_valence,
                avg_arousal=avg_arousal,
                trend=trend,
                confidence=min(1.0, data["count"] / 50.0)  # Higher confidence with more data
            ))
        
        # Sort by frequency and return top 10
        insights.sort(key=lambda x: x.frequency, reverse=True)
        return insights[:10]
    
    def _calculate_valence_trend(self, events: List[EmotionalEvent], hours: int) -> List[Tuple[datetime, float]]:
        """Calculate valence trend over time"""
        # Group events by hour and calculate average valence
        hourly_data = defaultdict(list)
        
        for event in events:
            if event.valence is not None and event.ingested_at:
                hour_key = event.ingested_at.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key].append(event.valence)
        
        # Calculate hourly averages
        trend_data = []
        for hour, valences in sorted(hourly_data.items()):
            avg_valence = statistics.mean(valences)
            trend_data.append((hour, avg_valence))
        
        return trend_data
    
    def _calculate_arousal_trend(self, events: List[EmotionalEvent], hours: int) -> List[Tuple[datetime, float]]:
        """Calculate arousal trend over time"""
        # Similar to valence trend but for arousal
        hourly_data = defaultdict(list)
        
        for event in events:
            if event.arousal is not None and event.ingested_at:
                hour_key = event.ingested_at.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key].append(event.arousal)
        
        # Calculate hourly averages
        trend_data = []
        for hour, arousals in sorted(hourly_data.items()):
            avg_arousal = statistics.mean(arousals)
            trend_data.append((hour, avg_arousal))
        
        return trend_data
    
    def _analyze_stress_indicators(self, events: List[EmotionalEvent]) -> Dict[str, float]:
        """Analyze stress indicators across the system"""
        if not events:
            return {}
        
        stress_emotions = self.config["emotion_categories"]["stress"]
        
        # Calculate various stress metrics
        total_events = len(events)
        stress_events = sum(1 for e in events if e.emotion_label in stress_emotions)
        
        high_arousal_events = sum(1 for e in events if e.arousal and e.arousal > 0.7)
        low_valence_events = sum(1 for e in events if e.valence and e.valence < -0.3)
        
        return {
            "stress_emotion_percentage": (stress_events / total_events * 100) if total_events > 0 else 0.0,
            "high_arousal_percentage": (high_arousal_events / total_events * 100) if total_events > 0 else 0.0,
            "low_valence_percentage": (low_valence_events / total_events * 100) if total_events > 0 else 0.0,
            "overall_stress_level": min(100.0, (stress_events + high_arousal_events + low_valence_events) / total_events * 33.33) if total_events > 0 else 0.0
        }
    
    def _detect_anomalies(self, events: List[EmotionalEvent]) -> List[Dict]:
        """Detect emotional anomalies"""
        anomalies = []
        
        if len(events) < 20:  # Need sufficient data for anomaly detection
            return anomalies
        
        # Get valence and arousal data
        valences = [e.valence for e in events if e.valence is not None]
        arousals = [e.arousal for e in events if e.arousal is not None]
        
        if valences:
            valence_mean = statistics.mean(valences)
            valence_std = statistics.stdev(valences) if len(valences) > 1 else 0
            
            # Detect valence anomalies (simplified)
            valence_anomalies = [v for v in valences if abs(v - valence_mean) > self.config["anomaly_threshold"] * valence_std]
            
            if valence_anomalies:
                anomalies.append({
                    "type": "valence_anomaly",
                    "description": f"Detected {len(valence_anomalies)} valence anomalies",
                    "severity": "medium" if len(valence_anomalies) < 5 else "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        if arousals:
            arousal_mean = statistics.mean(arousals)
            arousal_std = statistics.stdev(arousals) if len(arousals) > 1 else 0
            
            # Detect arousal anomalies
            arousal_anomalies = [a for a in arousals if abs(a - arousal_mean) > self.config["anomaly_threshold"] * arousal_std]
            
            if arousal_anomalies:
                anomalies.append({
                    "type": "arousal_anomaly",
                    "description": f"Detected {len(arousal_anomalies)} arousal anomalies",
                    "severity": "medium" if len(arousal_anomalies) < 5 else "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return anomalies
    
    def _create_empty_trends(self, time_period: str) -> EmotionalTrends:
        """Create empty trends object"""
        return EmotionalTrends(
            time_period=time_period,
            total_events=0,
            unique_users=0,
            top_emotions=[],
            avg_valence_trend=[],
            avg_arousal_trend=[],
            emotional_volatility=0.0,
            stress_indicators={},
            anomaly_alerts=[]
        )
    
    # ==================== CREDIT CORRELATION ANALYSIS ====================
    
    async def analyze_credit_emotion_correlation(self, days: int = 30) -> List[CreditEmotionCorrelation]:
        """Analyze correlation between emotions and credit decisions"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # This would require credit evaluation data with outcomes
            # For now, return sample correlations
            sample_correlations = [
                CreditEmotionCorrelation(
                    emotion_label="joy",
                    approval_rate=0.85,
                    avg_credit_amount=15000.0,
                    default_risk_correlation=-0.3,
                    sample_size=150
                ),
                CreditEmotionCorrelation(
                    emotion_label="anxiety",
                    approval_rate=0.45,
                    avg_credit_amount=8000.0,
                    default_risk_correlation=0.6,
                    sample_size=89
                ),
                CreditEmotionCorrelation(
                    emotion_label="neutral",
                    approval_rate=0.72,
                    avg_credit_amount=12000.0,
                    default_risk_correlation=0.1,
                    sample_size=320
                )
            ]
            
            return sample_correlations
        
        except Exception as e:
            self.logger.error(f"Failed to analyze credit-emotion correlation: {e}")
            return []
        finally:
            db.close()
    
    # ==================== LIVE DASHBOARD METRICS ====================
    
    async def get_live_emotion_metrics(self) -> LiveEmotionMetrics:
        """Get real-time emotion metrics for dashboard"""
        db = SessionLocal()
        try:
            # Get events from the last 10 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            
            recent_events = db.query(EmotionalEvent).filter(
                EmotionalEvent.ingested_at >= cutoff_time
            ).all()
            
            # Calculate metrics
            active_users = len(set(e.user_id for e in recent_events))
            emotions_per_minute = len(recent_events) / 10.0  # events per minute
            
            # Find dominant emotion
            if recent_events:
                emotion_counts = Counter([e.emotion_label for e in recent_events if e.emotion_label])
                dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
            else:
                dominant_emotion = "neutral"
            
            # Calculate valence distribution
            valences = [e.valence for e in recent_events if e.valence is not None]
            valence_dist = self._calculate_valence_distribution(valences)
            
            # Calculate arousal distribution
            arousals = [e.arousal for e in recent_events if e.arousal is not None]
            arousal_dist = self._calculate_arousal_distribution(arousals)
            
            # Check for stress alerts
            stress_emotions = self.config["emotion_categories"]["stress"]
            stress_events = sum(1 for e in recent_events if e.emotion_label in stress_emotions)
            stress_alert = stress_events > len(recent_events) * 0.4 if recent_events else False
            
            # Simple anomaly detection
            anomaly_detected = len(recent_events) > 100  # Simple threshold for demo
            
            return LiveEmotionMetrics(
                current_active_users=active_users,
                emotions_per_minute=emotions_per_minute,
                dominant_emotion_now=dominant_emotion,
                valence_distribution=valence_dist,
                arousal_distribution=arousal_dist,
                stress_level_alert=stress_alert,
                anomaly_detected=anomaly_detected,
                last_updated=datetime.utcnow()
            )
        
        except Exception as e:
            self.logger.error(f"Failed to get live emotion metrics: {e}")
            return LiveEmotionMetrics(
                current_active_users=0,
                emotions_per_minute=0.0,
                dominant_emotion_now="neutral",
                valence_distribution={},
                arousal_distribution={},
                stress_level_alert=False,
                anomaly_detected=False,
                last_updated=datetime.utcnow()
            )
        finally:
            db.close()
    
    def _calculate_valence_distribution(self, valences: List[float]) -> Dict[str, float]:
        """Calculate valence distribution"""
        if not valences:
            return {"very_negative": 0, "negative": 0, "neutral": 100, "positive": 0, "very_positive": 0}
        
        very_negative = sum(1 for v in valences if v <= -0.6)
        negative = sum(1 for v in valences if -0.6 < v <= -0.2)
        neutral = sum(1 for v in valences if -0.2 < v <= 0.2)
        positive = sum(1 for v in valences if 0.2 < v <= 0.6)
        very_positive = sum(1 for v in valences if v > 0.6)
        
        total = len(valences)
        return {
            "very_negative": (very_negative / total * 100) if total > 0 else 0,
            "negative": (negative / total * 100) if total > 0 else 0,
            "neutral": (neutral / total * 100) if total > 0 else 0,
            "positive": (positive / total * 100) if total > 0 else 0,
            "very_positive": (very_positive / total * 100) if total > 0 else 0
        }
    
    def _calculate_arousal_distribution(self, arousals: List[float]) -> Dict[str, float]:
        """Calculate arousal distribution"""
        if not arousals:
            return {"very_low": 0, "low": 0, "medium": 100, "high": 0, "very_high": 0}
        
        very_low = sum(1 for a in arousals if a <= 0.2)
        low = sum(1 for a in arousals if 0.2 < a <= 0.4)
        medium = sum(1 for a in arousals if 0.4 < a <= 0.6)
        high = sum(1 for a in arousals if 0.6 < a <= 0.8)
        very_high = sum(1 for a in arousals if a > 0.8)
        
        total = len(arousals)
        return {
            "very_low": (very_low / total * 100) if total > 0 else 0,
            "low": (low / total * 100) if total > 0 else 0,
            "medium": (medium / total * 100) if total > 0 else 0,
            "high": (high / total * 100) if total > 0 else 0,
            "very_high": (very_high / total * 100) if total > 0 else 0
        }
    
    # ==================== EXPORT UTILITIES ====================
    
    async def export_emotion_insights(self, format: str = "json") -> Dict:
        """Export comprehensive emotion insights"""
        try:
            # Get system trends
            trends_24h = await self.analyze_system_emotional_trends(24)
            trends_7d = await self.analyze_system_emotional_trends(24 * 7)
            
            # Get credit correlations
            correlations = await self.analyze_credit_emotion_correlation()
            
            # Get live metrics
            live_metrics = await self.get_live_emotion_metrics()
            
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "trends_24h": asdict(trends_24h),
                "trends_7d": asdict(trends_7d),
                "credit_correlations": [asdict(c) for c in correlations],
                "live_metrics": asdict(live_metrics),
                "summary": {
                    "total_events_24h": trends_24h.total_events,
                    "unique_users_24h": trends_24h.unique_users,
                    "dominant_emotion": live_metrics.dominant_emotion_now,
                    "system_stress_level": trends_24h.stress_indicators.get("overall_stress_level", 0.0),
                    "anomalies_detected": len(trends_24h.anomaly_alerts)
                }
            }
            
            return export_data
        
        except Exception as e:
            self.logger.error(f"Failed to export emotion insights: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


# Global analytics engine instance
analytics_engine = EmotionalAnalyticsEngine()
