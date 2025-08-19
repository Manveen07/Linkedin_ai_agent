# backend/app/models/trends.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..database import Base

class IndustryTrends(Base):
    __tablename__ = "industry_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    industry = Column(String(100), nullable=False, index=True)
    
    # Trend data
    trend_title = Column(String(300), nullable=False)
    trend_description = Column(Text)
    trend_keywords = Column(JSON, default=list)  # Related keywords
    trend_source = Column(String(200))  # News API, web scraping, etc.
    
    # Relevance and popularity
    popularity_score = Column(Integer, default=0)  # 1-100
    relevance_score = Column(Integer, default=0)  # AI-calculated relevance
    
    # Content suggestions
    suggested_angles = Column(JSON, default=list)  # Content angles for this trend
    hashtags = Column(JSON, default=list)  # Trending hashtags
    
    # Metadata
    date_discovered = Column(DateTime(timezone=True), server_default=func.now())
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # External links
    source_urls = Column(JSON, default=list)

