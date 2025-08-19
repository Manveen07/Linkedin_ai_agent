# backend/app/models/versions.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class PostVersion(Base):
    __tablename__ = "post_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Version details
    version_name = Column(String(100))  # "Version A", "Version B"
    content = Column(Text, nullable=False)
    hashtags = Column(JSON, default=list)
    
    # A/B test results
    is_winner = Column(Boolean, default=False)
    performance_score = Column(Integer, default=0)
    test_results = Column(JSON, default=dict)  # Detailed A/B test metrics
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    original_post = relationship("Post")
    user = relationship("User")
