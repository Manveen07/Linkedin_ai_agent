# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String(100), unique=True, index=True, nullable=True)
    email = Column(String(100), unique=True, index=True)
    name = Column(String(100), nullable=False)
    headline = Column(String(300))
    industry = Column(String(100))
    current_role = Column(String(200))
    company = Column(String(200))
    location = Column(String(100))
    hashed_password = Column(String(200), nullable=False)  
    
    # Profile data as JSON
    skills = Column(JSON, default=list)
    experience = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    
    # AI personalization settings
    brand_voice = Column(String(50), default="professional")
    content_preferences = Column(JSON, default=dict)
    posting_schedule = Column(JSON, default=dict)
    
    # Account status
    is_active = Column(Boolean, default=True)
    linkedin_connected = Column(Boolean, default=False)
    access_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    
    # Relationships
    posts = relationship("Post", back_populates="user")
    analytics = relationship("PostAnalytics", back_populates="user")
    calendar = relationship("ContentCalendar", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    post_versions = relationship("PostVersion", back_populates="user")




