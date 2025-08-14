from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    credit_limit = Column(Float, default=0.0)
    credit_type = Column(String, default="Short-Term")

    transactions = relationship("Transaction", back_populates="user")
    emotional_events = relationship("EmotionalEvent", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime)

    user = relationship("User", back_populates="transactions")


class EmotionalEvent(Base):
    __tablename__ = "emotional_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    emotion = Column(String, nullable=False)
    intensity = Column(Float)
    timestamp = Column(DateTime)

    user = relationship("User", back_populates="emotional_events")
