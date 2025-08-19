# backend/app/models/post.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content details
    content = Column(Text, nullable=False)
    post_type = Column(String(50), default="text")
    hashtags = Column(JSON, default=list)
    mentions = Column(JSON, default=list)
    
    # Media attachments
    media_urls = Column(JSON, default=list)
    carousel_data = Column(JSON, default=dict)
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    published_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="draft")
    
    # LinkedIn integration
    linkedin_post_id = Column(String(100), nullable=True, unique=True)
    linkedin_url = Column(String(500), nullable=True)
    
    # AI generation metadata
    ai_prompt_used = Column(Text, nullable=True)
    generation_model = Column(String(50), default="gpt-4")
    topics_used = Column(JSON, default=list)
    
    # Performance prediction
    predicted_engagement = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="posts")
    user = relationship("User", back_populates="posts")
    analytics = relationship("PostAnalytics", back_populates="post", uselist=False)
    versions = relationship("PostVersion", back_populates="original_post")
