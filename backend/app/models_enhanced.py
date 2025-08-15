"""
Enhanced Database Models for CloudWalk Empathic Credit System

This module defines the complete database schema including:
- User profiles with credit information
- Transaction history for financial analysis  
- Emotional events for empathic credit decisions
- Credit evaluation history for ML model tracking

Designed for PostgreSQL with proper indexing for efficient queries.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Index, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.db import Base

class User(Base):
    """
    User Profile Database Table
    
    Stores comprehensive user profiles including:
    - Personal information
    - Current credit limits and types
    - Relationship to transaction history and emotional data
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Profile Information
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Credit Information
    credit_limit = Column(Float, default=0.0, nullable=False)
    credit_type = Column(String(50), default="Short-Term", nullable=False)  # Short-Term, Long-Term, Rejected
    last_credit_evaluation = Column(DateTime(timezone=True), nullable=True)
    credit_score = Column(Float, nullable=True)  # Last ML model risk score
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    risk_category = Column(String(20), default="Medium", nullable=False)  # Low, Medium, High
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    emotional_events = relationship("EmotionalEvent", back_populates="user", cascade="all, delete-orphan")
    credit_evaluations = relationship("CreditEvaluation", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    """
    Transaction History Database Table
    
    Stores all user financial transactions for credit evaluation.
    Optimized for querying transaction patterns and amounts.
    """
    __tablename__ = "transactions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction Details
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # credit, debit, transfer
    description = Column(Text, nullable=True)
    merchant_category = Column(String(100), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="transactions")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_user_transaction_date', 'user_id', 'timestamp'),
        Index('idx_transaction_amount_date', 'amount', 'timestamp'),
        Index('idx_user_transaction_type', 'user_id', 'transaction_type'),
    )


class EmotionalEvent(Base):
    """
    Emotional Data Database Table
    
    Stores real-time emotional data from various sources.
    Optimized for time-series analysis and user emotion patterns.
    """
    __tablename__ = "emotional_events"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    # Session and Source Information
    session_id = Column(String(255), index=True, nullable=True)
    source = Column(String(50), nullable=True, index=True)  # "text", "voice", "face", "survey", "api"
    
    # Emotional Analysis Results
    emotion_label = Column(String(50), nullable=True, index=True)  # "joy", "anger", "sadness", etc.
    valence = Column(Float, nullable=True)  # [-1..1] negative to positive
    arousal = Column(Float, nullable=True)  # [0..1] low to high intensity
    confidence = Column(Float, nullable=True)  # [0..1] model confidence
    
    # Additional Context
    context = Column(Text, nullable=True)  # Optional context description
    raw_payload = Column(JSONB, nullable=True)  # Raw flexible message data

    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=True)  # Original event timestamp
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="emotional_events")
    
    # Indexes for efficient time-series queries
    __table_args__ = (
        Index('idx_user_emotion_time', 'user_id', 'ingested_at'),
        Index('idx_user_emotion_label', 'user_id', 'emotion_label'),
        Index('idx_emotion_valence_arousal', 'valence', 'arousal'),
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_emotion_source_time', 'source', 'ingested_at'),
    )


class CreditEvaluation(Base):
    """
    Credit Evaluation History Table
    
    Stores historical credit evaluations and ML model results.
    Tracks credit decision history and risk score changes over time.
    """
    __tablename__ = "credit_evaluations"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # ML Model Results
    risk_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    features_used = Column(JSONB, nullable=False)  # Store the features used for evaluation
    
    # Credit Decision
    approved = Column(Boolean, nullable=False)
    credit_limit_offered = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    credit_type = Column(String(50), nullable=True)
    
    # Decision Context
    evaluation_reason = Column(String(255), nullable=True)  # Manual, Scheduled, Application
    decision_factors = Column(JSONB, nullable=True)  # Additional decision context
    
    # Timestamps
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="credit_evaluations")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_user_evaluation_time', 'user_id', 'evaluated_at'),
        Index('idx_risk_score_time', 'risk_score', 'evaluated_at'),
        Index('idx_approval_time', 'approved', 'evaluated_at'),
        Index('idx_model_version', 'model_version'),
    )
