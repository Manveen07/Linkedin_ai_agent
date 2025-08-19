# backend/app/models/settings.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # AI behavior settings
    content_tone = Column(String(50), default="professional")
    creativity_level = Column(Integer, default=7)  # 1-10 scale
    engagement_focus = Column(String(100), default="balanced")  # engagement, reach, quality
    
    # Posting preferences
    auto_post = Column(Boolean, default=False)
    review_before_posting = Column(Boolean, default=True)
    optimal_posting_times = Column(JSON, default=list)
    posting_frequency = Column(String(50), default="3-times-weekly")
    
    # Content preferences
    preferred_post_length = Column(String(50), default="medium")  # short, medium, long
    include_questions = Column(Boolean, default=True)
    include_call_to_action = Column(Boolean, default=True)
    avoid_topics = Column(JSON, default=list)  # Topics to avoid
    
    # Privacy and compliance
    content_review_enabled = Column(Boolean, default=True)
    compliance_check = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
