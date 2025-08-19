# backend/app/models/calendar.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ContentCalendar(Base):
    __tablename__ = "content_calendar"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Calendar details
    calendar_month = Column(Integer, nullable=False)  # 1-12
    calendar_year = Column(Integer, nullable=False)
    
    # Content strategy
    monthly_theme = Column(String(200), nullable=True)
    weekly_themes = Column(JSON, default=dict)  # {1: "Innovation", 2: "Leadership"}
    content_goals = Column(JSON, default=list)  # ["thought leadership", "engagement"]
    
    # Posting schedule
    scheduled_posts = Column(JSON, default=dict)  # {date: post_id}
    suggested_topics = Column(JSON, default=list)  # AI-suggested topics for the month
    
    # Performance targets
    engagement_target = Column(Integer, default=0)
    follower_growth_target = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

