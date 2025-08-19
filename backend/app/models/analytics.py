# backend/app/models/analytics.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class PostAnalytics(Base):
    __tablename__ = "post_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True)
    
    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0)
    
    # Engagement rate calculation
    engagement_rate = Column(String(10), default="0%")
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    
    # Audience insights
    audience_data = Column(JSON, default=dict)
    top_countries = Column(JSON, default=list)
    peak_engagement_time = Column(DateTime(timezone=True), nullable=True)
    
    # Performance tracking over time
    metrics_history = Column(JSON, default=list)
    
    # Timestamps
    first_tracked = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    post = relationship("Post")

