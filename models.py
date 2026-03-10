from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    alerts = relationship("AlertLog", back_populates="user")

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    alert_type = Column(String, index=True)
    message = Column(String)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float)
    model_source = Column(String)
    
    user = relationship("User", back_populates="alerts")
