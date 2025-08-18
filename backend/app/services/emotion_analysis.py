"""
Emotion Analysis Service

Advanced emotion analysis and pattern recognition for real-time processing
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmotionContext:
    """Context for emotion analysis"""
    user_id: int
    session_id: str
    location: Optional[Dict[str, Any]] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    activity: Optional[str] = None
    social_context: Optional[str] = None

@dataclass
class EmotionPattern:
    """Detected emotion pattern"""
    pattern_type: str
    confidence: float
    description: str
    recommendations: List[str]
    risk_level: str  # "low", "medium", "high"

class EmotionAnalyzer:
    """Advanced emotion analysis engine"""
    
    def __init__(self):
        self.emotion_clusters = {
            'positive_low_arousal': ['contentment', 'calm', 'relaxed', 'peaceful'],
            'positive_high_arousal': ['joy', 'excitement', 'enthusiasm', 'euphoria'],
            'negative_low_arousal': ['sadness', 'boredom', 'fatigue', 'melancholy'],
            'negative_high_arousal': ['anger', 'fear', 'anxiety', 'frustration'],
            'neutral': ['neutral', 'indifferent', 'composed']
        }
        
        # Emotional state risk indicators
        self.risk_patterns = {
            'high_stress': {
                'valence_range': (-1.0, -0.3),
                'arousal_range': (0.7, 1.0),
                'risk_level': 'high'
            },
            'depression_indicators': {
                'valence_range': (-1.0, -0.4),
                'arousal_range': (0.0, 0.3),
                'risk_level': 'high'
            },
            'anxiety_pattern': {
                'valence_range': (-0.6, 0.2),
                'arousal_range': (0.6, 1.0),
                'risk_level': 'medium'
            },
            'emotional_volatility': {
                'valence_std_threshold': 0.6,
                'arousal_std_threshold': 0.5,
                'risk_level': 'medium'
            }
        }
        
    def analyze_emotion_state(self, 
                            valence: float, 
                            arousal: float, 
                            emotion_label: Optional[str] = None) -> Dict[str, Any]:
        """Analyze current emotional state"""
        
        # Determine quadrant
        quadrant = self._get_emotion_quadrant(valence, arousal)
        
        # Calculate emotion intensity
        intensity = np.sqrt(valence**2 + arousal**2)
        
        # Determine emotional cluster
        cluster = self._get_emotion_cluster(valence, arousal)
        
        # Assess risk level
        risk_assessment = self._assess_risk_level(valence, arousal)
        
        return {
            'quadrant': quadrant,
            'cluster': cluster,
            'intensity': round(intensity, 3),
            'risk_assessment': risk_assessment,
            'recommendations': self._get_recommendations(valence, arousal, cluster)
        }
    
    def analyze_emotion_trajectory(self, 
                                 emotion_history: List[Dict[str, Any]], 
                                 window_size: int = 10) -> Dict[str, Any]:
        """Analyze emotion trajectory over time"""
        
        if len(emotion_history) < 2:
            return {'status': 'insufficient_data'}
        
        # Extract recent emotions
        recent = emotion_history[-window_size:]
        
        valences = [e.get('valence') for e in recent if e.get('valence') is not None]
        arousals = [e.get('arousal') for e in recent if e.get('arousal') is not None]
        timestamps = [e.get('timestamp') for e in recent if e.get('timestamp')]
        
        if len(valences) < 2:
            return {'status': 'insufficient_data'}
        
        # Calculate trends
        valence_trend = self._calculate_trend(valences)
        arousal_trend = self._calculate_trend(arousals)
        
        # Calculate stability
        valence_stability = 1.0 - min(np.std(valences), 1.0)
        arousal_stability = 1.0 - min(np.std(arousals), 1.0)
        overall_stability = (valence_stability + arousal_stability) / 2
        
        # Detect patterns
        patterns = self._detect_patterns(recent)
        
        # Calculate emotional velocity (rate of change)
        velocity = self._calculate_emotional_velocity(valences, arousals, timestamps)
        
        return {
            'valence_trend': valence_trend,
            'arousal_trend': arousal_trend,
            'stability_score': round(overall_stability, 3),
            'patterns': patterns,
            'emotional_velocity': velocity,
            'summary': self._generate_trajectory_summary(valence_trend, arousal_trend, patterns)
        }
    
    def detect_anomalies(self, 
                        emotion_history: List[Dict[str, Any]], 
                        baseline_window: int = 50) -> List[Dict[str, Any]]:
        """Detect emotional anomalies"""
        
        if len(emotion_history) < baseline_window:
            return []
        
        anomalies = []
        
        # Establish baseline
        baseline = emotion_history[-baseline_window:-10]  # Exclude recent events
        recent = emotion_history[-10:]  # Recent events to check
        
        baseline_valences = [e.get('valence') for e in baseline if e.get('valence') is not None]
        baseline_arousals = [e.get('arousal') for e in baseline if e.get('arousal') is not None]
        
        if not baseline_valences or not baseline_arousals:
            return []
        
        baseline_val_mean = np.mean(baseline_valences)
        baseline_val_std = np.std(baseline_valences)
        baseline_ar_mean = np.mean(baseline_arousals)
        baseline_ar_std = np.std(baseline_arousals)
        
        # Check recent events for anomalies
        for event in recent:
            valence = event.get('valence')
            arousal = event.get('arousal')
            
            if valence is None or arousal is None:
                continue
            
            # Z-score based anomaly detection
            val_zscore = abs(valence - baseline_val_mean) / (baseline_val_std + 1e-6)
            ar_zscore = abs(arousal - baseline_ar_mean) / (baseline_ar_std + 1e-6)
            
            # Threshold for anomaly (2.5 standard deviations)
            if val_zscore > 2.5 or ar_zscore > 2.5:
                anomalies.append({
                    'timestamp': event.get('timestamp'),
                    'type': 'statistical_outlier',
                    'valence_zscore': round(val_zscore, 3),
                    'arousal_zscore': round(ar_zscore, 3),
                    'severity': 'high' if max(val_zscore, ar_zscore) > 3.0 else 'medium'
                })
        
        return anomalies
    
    def _get_emotion_quadrant(self, valence: float, arousal: float) -> str:
        """Determine emotion quadrant"""
        if valence >= 0 and arousal >= 0.5:
            return "high_positive"  # Joy, excitement
        elif valence >= 0 and arousal < 0.5:
            return "low_positive"   # Calm, content
        elif valence < 0 and arousal >= 0.5:
            return "high_negative"  # Anger, fear
        else:
            return "low_negative"   # Sadness, boredom
    
    def _get_emotion_cluster(self, valence: float, arousal: float) -> str:
        """Get emotion cluster based on valence-arousal"""
        if valence > 0.3:
            return 'positive_high_arousal' if arousal > 0.5 else 'positive_low_arousal'
        elif valence < -0.3:
            return 'negative_high_arousal' if arousal > 0.5 else 'negative_low_arousal'
        else:
            return 'neutral'
    
    def _assess_risk_level(self, valence: float, arousal: float) -> Dict[str, Any]:
        """Assess psychological risk level"""
        risks = []
        overall_risk = "low"
        
        for pattern_name, criteria in self.risk_patterns.items():
            if 'valence_range' in criteria and 'arousal_range' in criteria:
                val_min, val_max = criteria['valence_range']
                ar_min, ar_max = criteria['arousal_range']
                
                if val_min <= valence <= val_max and ar_min <= arousal <= ar_max:
                    risks.append({
                        'pattern': pattern_name,
                        'risk_level': criteria['risk_level']
                    })
                    if criteria['risk_level'] == 'high':
                        overall_risk = 'high'
                    elif criteria['risk_level'] == 'medium' and overall_risk == 'low':
                        overall_risk = 'medium'
        
        return {
            'overall_risk': overall_risk,
            'specific_risks': risks,
            'recommendation': self._get_risk_recommendation(overall_risk)
        }
    
    def _get_recommendations(self, valence: float, arousal: float, cluster: str) -> List[str]:
        """Get recommendations based on emotional state"""
        recommendations = []
        
        if cluster == 'negative_high_arousal':
            recommendations.extend([
                "Consider relaxation techniques",
                "Take deep breaths",
                "Step away from stressful situation if possible"
            ])
        elif cluster == 'negative_low_arousal':
            recommendations.extend([
                "Engage in light physical activity",
                "Connect with supportive friends",
                "Consider professional support if persistent"
            ])
        elif cluster == 'positive_low_arousal':
            recommendations.extend([
                "Enjoy this peaceful moment",
                "Practice mindfulness",
                "Maintain current activities"
            ])
        elif cluster == 'positive_high_arousal':
            recommendations.extend([
                "Channel energy into productive activities",
                "Share positive feelings with others",
                "Maintain balance to avoid burnout"
            ])
        
        return recommendations
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend in values"""
        if len(values) < 2:
            return {'direction': 'stable', 'strength': 0.0}
        
        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        direction = 'stable'
        if slope > 0.05:
            direction = 'increasing'
        elif slope < -0.05:
            direction = 'decreasing'
        
        return {
            'direction': direction,
            'strength': round(abs(slope), 3),
            'slope': round(slope, 3)
        }
    
    def _detect_patterns(self, emotion_history: List[Dict[str, Any]]) -> List[str]:
        """Detect specific emotion patterns"""
        patterns = []
        
        if len(emotion_history) < 3:
            return patterns
        
        valences = [e.get('valence') for e in emotion_history if e.get('valence') is not None]
        arousals = [e.get('arousal') for e in emotion_history if e.get('arousal') is not None]
        emotions = [e.get('emotion_label') for e in emotion_history if e.get('emotion_label')]
        
        # Consistency pattern
        if len(set(emotions[-5:])) <= 2 and len(emotions) >= 5:
            patterns.append('emotional_consistency')
        
        # Volatility pattern
        if len(valences) >= 5:
            val_std = np.std(valences[-5:])
            if val_std > 0.5:
                patterns.append('high_volatility')
        
        # Cycle detection (simplified)
        if len(valences) >= 6:
            # Look for alternating patterns
            recent_val = valences[-6:]
            if self._is_alternating_pattern(recent_val):
                patterns.append('cyclical_emotions')
        
        return patterns
    
    def _is_alternating_pattern(self, values: List[float], threshold: float = 0.3) -> bool:
        """Detect alternating high-low pattern"""
        if len(values) < 4:
            return False
        
        changes = []
        for i in range(1, len(values)):
            changes.append(values[i] - values[i-1])
        
        # Check if signs alternate
        sign_changes = 0
        for i in range(1, len(changes)):
            if (changes[i] > threshold and changes[i-1] < -threshold) or \
               (changes[i] < -threshold and changes[i-1] > threshold):
                sign_changes += 1
        
        return sign_changes >= 2
    
    def _calculate_emotional_velocity(self, 
                                    valences: List[float], 
                                    arousals: List[float], 
                                    timestamps: List[Any]) -> Dict[str, float]:
        """Calculate rate of emotional change"""
        if len(valences) < 2 or len(timestamps) < 2:
            return {'valence_velocity': 0.0, 'arousal_velocity': 0.0}
        
        # Calculate time differences (assume timestamps are datetime strings)
        try:
            if isinstance(timestamps[0], str):
                times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
            else:
                times = timestamps
            
            time_diffs = [(times[i] - times[i-1]).total_seconds() for i in range(1, len(times))]
            val_diffs = [valences[i] - valences[i-1] for i in range(1, len(valences))]
            ar_diffs = [arousals[i] - arousals[i-1] for i in range(1, len(arousals))]
            
            val_velocity = np.mean([abs(vd/td) for vd, td in zip(val_diffs, time_diffs) if td > 0])
            ar_velocity = np.mean([abs(ad/td) for ad, td in zip(ar_diffs, time_diffs) if td > 0])
            
            return {
                'valence_velocity': round(val_velocity, 4),
                'arousal_velocity': round(ar_velocity, 4)
            }
        except:
            return {'valence_velocity': 0.0, 'arousal_velocity': 0.0}
    
    def _generate_trajectory_summary(self, 
                                   valence_trend: Dict[str, Any], 
                                   arousal_trend: Dict[str, Any], 
                                   patterns: List[str]) -> str:
        """Generate human-readable trajectory summary"""
        summary_parts = []
        
        # Valence trend
        if valence_trend['direction'] == 'increasing':
            summary_parts.append("mood improving")
        elif valence_trend['direction'] == 'decreasing':
            summary_parts.append("mood declining")
        else:
            summary_parts.append("mood stable")
        
        # Arousal trend
        if arousal_trend['direction'] == 'increasing':
            summary_parts.append("energy increasing")
        elif arousal_trend['direction'] == 'decreasing':
            summary_parts.append("energy decreasing")
        else:
            summary_parts.append("energy stable")
        
        # Patterns
        if 'high_volatility' in patterns:
            summary_parts.append("high emotional variability")
        if 'emotional_consistency' in patterns:
            summary_parts.append("consistent emotional state")
        if 'cyclical_emotions' in patterns:
            summary_parts.append("cyclical emotional pattern")
        
        return ", ".join(summary_parts)
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            'low': "Continue monitoring emotional wellbeing",
            'medium': "Consider stress management techniques and self-care",
            'high': "Strongly recommend seeking professional support or immediate intervention"
        }
        return recommendations.get(risk_level, "Monitor emotional state")
