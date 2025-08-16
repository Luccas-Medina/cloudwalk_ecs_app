from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    credit_limit = Column(Float, default=0.0)
    credit_type = Column(String, default="Short-Term")

    transactions = relationship("Transaction", back_populates="user")
    emotional_events = relationship("EmotionalEvent", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime)

    user = relationship("User", back_populates="transactions")


class EmotionalEvent(Base):
    __tablename__ = "emotional_events"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    session_id = Column(String, index=True, nullable=True)
    source = Column(String, nullable=True)           # "text" | "voice" | "face" | "survey" | etc.
    emotion_label = Column(String, nullable=True)    # "joy" | "anger" | ...
    valence = Column(Float, nullable=True)           # [-1..1] or [0..1], your choice
    arousal = Column(Float, nullable=True)           # [0..1]
    confidence = Column(Float, nullable=True)        # [0..1]
    raw_payload = Column(JSONB, nullable=True)       # raw flexible message

    timestamp = Column(DateTime(timezone=True), nullable=True)  # event’s own ts (if provided)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="emotional_events")