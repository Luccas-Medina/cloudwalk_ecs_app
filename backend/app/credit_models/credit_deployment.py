# app/models/credit_deployment.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class CreditOfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    FAILED = "failed"
    EXPIRED = "expired"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"

class CreditOffer(Base):
    """Credit offers pending user acceptance"""
    __tablename__ = "credit_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Offer details
    offered_limit = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    credit_score_used = Column(Integer, nullable=True)
    
    # ML model info
    model_version = Column(String(50), nullable=False)
    risk_assessment = Column(JSON, nullable=True)  # ML model output
    emotional_context = Column(JSON, nullable=True)  # Emotion data at time of offer
    
    # Status tracking
    status = Column(String(20), default=CreditOfferStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    
    # Deployment tracking
    deployment_task_id = Column(String(255), nullable=True)
    deployment_attempts = Column(Integer, default=0)
    deployment_error = Column(Text, nullable=True)
    
    # Relationships
    deployment_events = relationship("CreditDeploymentEvent", back_populates="offer")
    notifications = relationship("CreditNotification", back_populates="offer")

class CreditDeploymentEvent(Base):
    """Audit trail for credit deployment process"""
    __tablename__ = "credit_deployment_events"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("credit_offers.id"), nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # offer_created, accepted, deployed, etc.
    event_data = Column(JSON, nullable=True)
    
    # Processing info
    task_id = Column(String(255), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    worker_id = Column(String(100), nullable=True)
    
    # Status
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    offer = relationship("CreditOffer", back_populates="deployment_events")

class CreditNotification(Base):
    """Mobile app notifications for credit events"""
    __tablename__ = "credit_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("credit_offers.id"), nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # offer_ready, deployed, failed
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    deep_link = Column(String(500), nullable=True)  # App deep link
    
    # Delivery tracking
    status = Column(String(20), default=NotificationStatus.PENDING, nullable=False)
    device_token = Column(String(500), nullable=True)
    platform = Column(String(20), nullable=True)  # ios, android
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Response tracking
    push_notification_id = Column(String(255), nullable=True)
    delivery_response = Column(JSON, nullable=True)
    
    # Relationships
    offer = relationship("CreditOffer", back_populates="notifications")

class UserCreditProfile(Base):
    """User's current credit profile and limits"""
    __tablename__ = "user_credit_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    
    # Current credit status
    current_limit = Column(Float, default=0.0, nullable=False)
    available_credit = Column(Float, default=0.0, nullable=False)
    used_credit = Column(Float, default=0.0, nullable=False)
    
    # Credit terms
    current_interest_rate = Column(Float, nullable=True)
    
    # Profile metadata
    credit_score = Column(Integer, nullable=True)
    risk_category = Column(String(20), nullable=True)  # low, medium, high
    
    # Emotional intelligence insights
    emotional_stability_score = Column(Float, nullable=True)
    stress_indicators = Column(JSON, nullable=True)
    last_emotion_update = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_limit_increase = Column(DateTime, nullable=True)
