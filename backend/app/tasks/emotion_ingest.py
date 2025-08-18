from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json

from app.core.db import SessionLocal
from app.models import EmotionalEvent, User

from app.services.emotion_analysis import EmotionAnalyzer
import dateutil.parser as dtparse  # add python-dateutil to requirements if not present

# Configure logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, name="persist_emotion_event", max_retries=3, default_retry_delay=2)
def persist_emotion_event(self, event: dict):
    """
    Persist a normalized emotion event into the database.
    Retries on transient DB errors.
    """
    db: Session = SessionLocal()
    try:
        ts = event.get("timestamp")
        ev_ts = None
        if ts:
            try:
                ev_ts = dtparse.parse(ts)  # tolerate ISO strings
            except Exception:
                ev_ts = None

        row = EmotionalEvent(
            user_id=event["user_id"],
            session_id=event.get("session_id"),
            source=event.get("source"),
            emotion_label=event.get("emotion_label"),
            valence=event.get("valence"),
            arousal=event.get("arousal"),
            confidence=event.get("confidence"),
            raw_payload=event.get("raw_payload"),
            timestamp=ev_ts,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        
        logger.info(f"Persisted emotion event: user={event['user_id']}, emotion={event.get('emotion_label')}")
        return {"status": "ok", "id": row.id}
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"Database error persisting emotion event: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "error": str(exc)}
    finally:
        db.close()

@shared_task(bind=True, name="analyze_emotion_patterns", max_retries=2, default_retry_delay=5)
def analyze_emotion_patterns(self, user_id: int, session_id: Optional[str] = None):
    """
    Analyze emotion patterns for a user session or overall user history.
    Performs advanced pattern recognition and anomaly detection.
    """
    db: Session = SessionLocal()
    analyzer = EmotionAnalyzer()
    
    try:
        # Get recent emotion events
        query = db.query(EmotionalEvent).filter(EmotionalEvent.user_id == user_id)
        
        if session_id:
            query = query.filter(EmotionalEvent.session_id == session_id)
            events = query.order_by(desc(EmotionalEvent.ingested_at)).limit(50).all()
        else:
            # Get events from last 24 hours for pattern analysis
            since = datetime.now() - timedelta(hours=24)
            events = query.filter(EmotionalEvent.ingested_at >= since)\
                         .order_by(desc(EmotionalEvent.ingested_at)).all()
        
        if len(events) < 3:
            return {"status": "insufficient_data", "event_count": len(events)}
        
        # Convert to analysis format
        emotion_data = []
        for event in events:
            emotion_data.append({
                'valence': event.valence,
                'arousal': event.arousal,
                'emotion_label': event.emotion_label,
                'timestamp': event.ingested_at.isoformat() if event.ingested_at else None,
                'source': event.source
            })
        
        # Perform trajectory analysis
        trajectory_analysis = analyzer.analyze_emotion_trajectory(emotion_data)
        
        # Detect anomalies if enough data
        anomalies = []
        if len(events) >= 20:
            anomalies = analyzer.detect_anomalies(emotion_data)
        
        # Analyze current emotional state (most recent event)
        current_event = events[0]
        current_state_analysis = {}
        if current_event.valence is not None and current_event.arousal is not None:
            current_state_analysis = analyzer.analyze_emotion_state(
                current_event.valence, 
                current_event.arousal, 
                current_event.emotion_label
            )
        
        # Generate insights and recommendations
        insights = generate_emotion_insights(trajectory_analysis, current_state_analysis, anomalies)
        
        analysis_result = {
            "user_id": user_id,
            "session_id": session_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "event_count": len(events),
            "current_state": current_state_analysis,
            "trajectory": trajectory_analysis,
            "anomalies": anomalies,
            "insights": insights,
            "recommendations": insights.get('recommendations', [])
        }
        
        logger.info(f"Completed emotion pattern analysis for user {user_id}, session {session_id}")
        return analysis_result
        
    except Exception as exc:
        logger.error(f"Error analyzing emotion patterns: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "error": str(exc)}
    finally:
        db.close()

@shared_task(name="detect_emotional_risk_users")
def detect_emotional_risk_users():
    """
    Background task to identify users showing concerning emotional patterns.
    Runs periodically to flag users who may need attention.
    """
    db: Session = SessionLocal()
    analyzer = EmotionAnalyzer()
    
    try:
        # Get users with recent emotional activity
        since = datetime.now() - timedelta(hours=12)
        
        users_with_activity = db.query(User.id).join(EmotionalEvent)\
            .filter(EmotionalEvent.ingested_at >= since)\
            .distinct().all()
        
        risk_users = []
        
        for (user_id,) in users_with_activity:
            # Get recent events for this user
            events = db.query(EmotionalEvent)\
                .filter(and_(EmotionalEvent.user_id == user_id,
                           EmotionalEvent.ingested_at >= since))\
                .order_by(desc(EmotionalEvent.ingested_at)).all()
            
            if len(events) < 5:
                continue
            
            # Convert to analysis format
            emotion_data = []
            for event in events:
                if event.valence is not None and event.arousal is not None:
                    emotion_data.append({
                        'valence': event.valence,
                        'arousal': event.arousal,
                        'emotion_label': event.emotion_label,
                        'timestamp': event.ingested_at.isoformat()
                    })
            
            if len(emotion_data) < 5:
                continue
            
            # Analyze for risk patterns
            trajectory = analyzer.analyze_emotion_trajectory(emotion_data)
            anomalies = analyzer.detect_anomalies(emotion_data)
            
            # Check for high-risk indicators
            risk_score = calculate_risk_score(emotion_data, trajectory, anomalies)
            
            if risk_score >= 0.7:  # High risk threshold
                risk_users.append({
                    'user_id': user_id,
                    'risk_score': risk_score,
                    'event_count': len(emotion_data),
                    'risk_factors': identify_risk_factors(emotion_data, trajectory, anomalies)
                })
        
        logger.info(f"Risk detection completed. Found {len(risk_users)} high-risk users")
        
        # In a real system, this would trigger alerts or notifications
        return {
            "status": "completed",
            "analysis_timestamp": datetime.now().isoformat(),
            "users_analyzed": len(users_with_activity),
            "high_risk_users": len(risk_users),
            "risk_users": risk_users
        }
        
    except Exception as exc:
        logger.error(f"Error in risk detection task: {exc}")
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()

@shared_task(name="generate_emotion_summary_report")
def generate_emotion_summary_report(user_id: int, days: int = 7):
    """
    Generate a comprehensive emotion summary report for a user.
    """
    db: Session = SessionLocal()
    analyzer = EmotionAnalyzer()
    
    try:
        # Get events for the specified period
        since = datetime.now() - timedelta(days=days)
        events = db.query(EmotionalEvent)\
            .filter(and_(EmotionalEvent.user_id == user_id,
                        EmotionalEvent.ingested_at >= since))\
            .order_by(EmotionalEvent.ingested_at).all()
        
        if not events:
            return {"status": "no_data", "user_id": user_id}
        
        # Convert to analysis format
        emotion_data = []
        for event in events:
            if event.valence is not None and event.arousal is not None:
                emotion_data.append({
                    'valence': event.valence,
                    'arousal': event.arousal,
                    'emotion_label': event.emotion_label,
                    'source': event.source,
                    'timestamp': event.ingested_at.isoformat()
                })
        
        # Calculate summary statistics
        valences = [e['valence'] for e in emotion_data]
        arousals = [e['arousal'] for e in emotion_data]
        emotions = [e['emotion_label'] for e in emotion_data if e['emotion_label']]
        sources = [e['source'] for e in emotion_data if e['source']]
        
        # Generate comprehensive report
        report = {
            "user_id": user_id,
            "period_days": days,
            "report_generated": datetime.now().isoformat(),
            "summary_stats": {
                "total_events": len(emotion_data),
                "avg_valence": round(sum(valences) / len(valences), 3) if valences else None,
                "avg_arousal": round(sum(arousals) / len(arousals), 3) if arousals else None,
                "valence_range": [round(min(valences), 3), round(max(valences), 3)] if valences else None,
                "arousal_range": [round(min(arousals), 3), round(max(arousals), 3)] if arousals else None,
                "dominant_emotion": max(set(emotions), key=emotions.count) if emotions else None,
                "emotion_diversity": len(set(emotions)) if emotions else 0,
                "primary_sources": list(set(sources)) if sources else []
            },
            "trajectory_analysis": analyzer.analyze_emotion_trajectory(emotion_data),
            "anomalies": analyzer.detect_anomalies(emotion_data) if len(emotion_data) >= 20 else [],
            "patterns": identify_long_term_patterns(emotion_data),
            "recommendations": generate_personalized_recommendations(emotion_data)
        }
        
        logger.info(f"Generated emotion summary report for user {user_id}")
        return report
        
    except Exception as exc:
        logger.error(f"Error generating emotion report: {exc}")
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()

def generate_emotion_insights(trajectory_analysis: Dict, 
                            current_state: Dict, 
                            anomalies: List[Dict]) -> Dict[str, Any]:
    """Generate actionable insights from emotion analysis"""
    insights = {
        "summary": "",
        "key_findings": [],
        "recommendations": [],
        "risk_level": "low"
    }
    
    # Analyze trajectory
    if trajectory_analysis.get('status') != 'insufficient_data':
        valence_trend = trajectory_analysis.get('valence_trend', {})
        stability = trajectory_analysis.get('stability_score', 1.0)
        patterns = trajectory_analysis.get('patterns', [])
        
        # Generate summary
        summary_parts = [trajectory_analysis.get('summary', '')]
        if stability < 0.5:
            summary_parts.append("showing high emotional variability")
        
        insights["summary"] = ", ".join(filter(None, summary_parts))
        
        # Key findings
        if valence_trend.get('direction') == 'decreasing':
            insights["key_findings"].append("Mood has been declining over recent period")
            insights["risk_level"] = "medium"
        
        if 'high_volatility' in patterns:
            insights["key_findings"].append("High emotional volatility detected")
            insights["risk_level"] = "medium"
        
        if stability < 0.3:
            insights["key_findings"].append("Very unstable emotional state")
            insights["risk_level"] = "high"
    
    # Analyze current state
    if current_state:
        risk_assessment = current_state.get('risk_assessment', {})
        if risk_assessment.get('overall_risk') == 'high':
            insights["risk_level"] = "high"
            insights["key_findings"].append("Current emotional state indicates high risk")
        
        insights["recommendations"].extend(current_state.get('recommendations', []))
    
    # Analyze anomalies
    if anomalies:
        high_severity_anomalies = [a for a in anomalies if a.get('severity') == 'high']
        if high_severity_anomalies:
            insights["key_findings"].append("Significant emotional anomalies detected")
            insights["risk_level"] = "high"
    
    return insights

def calculate_risk_score(emotion_data: List[Dict], 
                        trajectory: Dict, 
                        anomalies: List[Dict]) -> float:
    """Calculate overall emotional risk score"""
    risk_score = 0.0
    
    # Base risk from valence/arousal patterns
    valences = [e['valence'] for e in emotion_data]
    arousals = [e['arousal'] for e in emotion_data]
    
    if valences and arousals:
        avg_valence = sum(valences) / len(valences)
        avg_arousal = sum(arousals) / len(arousals)
        
        # High risk combinations
        if avg_valence < -0.4 and avg_arousal > 0.6:  # High stress
            risk_score += 0.4
        elif avg_valence < -0.5 and avg_arousal < 0.3:  # Depression indicators
            risk_score += 0.5
        
        # Volatility risk
        import numpy as np
        if len(valences) > 3:
            val_std = np.std(valences)
            ar_std = np.std(arousals)
            if val_std > 0.6 or ar_std > 0.5:
                risk_score += 0.3
    
    # Trajectory-based risk
    if trajectory.get('stability_score', 1.0) < 0.3:
        risk_score += 0.2
    
    # Anomaly-based risk
    high_severity_anomalies = [a for a in anomalies if a.get('severity') == 'high']
    risk_score += min(len(high_severity_anomalies) * 0.1, 0.3)
    
    return min(risk_score, 1.0)

def identify_risk_factors(emotion_data: List[Dict], 
                         trajectory: Dict, 
                         anomalies: List[Dict]) -> List[str]:
    """Identify specific risk factors"""
    factors = []
    
    valences = [e['valence'] for e in emotion_data]
    arousals = [e['arousal'] for e in emotion_data]
    
    if valences and arousals:
        avg_valence = sum(valences) / len(valences)
        avg_arousal = sum(arousals) / len(arousals)
        
        if avg_valence < -0.4:
            factors.append("persistently negative mood")
        if avg_arousal > 0.7:
            factors.append("consistently high arousal/stress")
        
        import numpy as np
        if len(valences) > 3 and np.std(valences) > 0.6:
            factors.append("high emotional volatility")
    
    if trajectory.get('stability_score', 1.0) < 0.3:
        factors.append("unstable emotional patterns")
    
    if len([a for a in anomalies if a.get('severity') == 'high']) > 0:
        factors.append("significant emotional anomalies")
    
    return factors

def identify_long_term_patterns(emotion_data: List[Dict]) -> List[str]:
    """Identify long-term emotional patterns"""
    patterns = []
    
    if len(emotion_data) < 10:
        return patterns
    
    # Analyze by time periods (if enough data)
    # This could be enhanced with more sophisticated time series analysis
    valences = [e['valence'] for e in emotion_data]
    
    # Simple trend analysis
    import numpy as np
    first_half = valences[:len(valences)//2]
    second_half = valences[len(valences)//2:]
    
    if len(first_half) > 0 and len(second_half) > 0:
        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)
        
        if second_avg - first_avg > 0.3:
            patterns.append("improving_trend")
        elif first_avg - second_avg > 0.3:
            patterns.append("declining_trend")
        else:
            patterns.append("stable_pattern")
    
    return patterns

def generate_personalized_recommendations(emotion_data: List[Dict]) -> List[str]:
    """Generate personalized recommendations based on emotion patterns"""
    recommendations = []
    
    valences = [e['valence'] for e in emotion_data]
    arousals = [e['arousal'] for e in emotion_data]
    sources = [e['source'] for e in emotion_data if e['source']]
    
    if not valences or not arousals:
        return ["Continue monitoring emotional wellbeing"]
    
    import numpy as np
    avg_valence = np.mean(valences)
    avg_arousal = np.mean(arousals)
    
    # Personalized recommendations based on patterns
    if avg_valence < -0.2 and avg_arousal > 0.5:
        recommendations.extend([
            "Consider stress reduction techniques",
            "Practice mindfulness or meditation",
            "Ensure adequate rest and sleep"
        ])
    elif avg_valence < -0.3 and avg_arousal < 0.4:
        recommendations.extend([
            "Engage in uplifting activities",
            "Connect with supportive friends/family",
            "Consider light exercise or outdoor activities"
        ])
    elif avg_valence > 0.3:
        recommendations.extend([
            "Maintain current positive practices",
            "Share positive energy with others",
            "Continue activities that bring joy"
        ])
    
    # Source-specific recommendations
    if 'text' in sources:
        recommendations.append("Consider the emotional impact of text communications")
    if 'voice' in sources:
        recommendations.append("Pay attention to vocal emotional patterns")
    
    return recommendations
