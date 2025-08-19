# backend/app/api/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..models.post import Post
from ..models.analytics import PostAnalytics  
from ..api.users import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Get ALL posts, not just published ones with analytics
    all_posts = db.query(Post).filter(
        Post.user_id == current_user.id,
        Post.created_at >= thirty_days_ago
    ).all()
    
    published_posts = [p for p in all_posts if p.status == "published"]
    
    # Calculate stats including posts without analytics
    total_likes = sum(p.analytics.likes_count if p.analytics else 0 for p in published_posts)
    total_comments = sum(p.analytics.comments_count if p.analytics else 0 for p in published_posts)
    total_shares = sum(p.analytics.shares_count if p.analytics else 0 for p in published_posts)
    
    return {
        "user_stats": {
            "total_posts": len(all_posts),
            "drafts": len([p for p in all_posts if p.status == "draft"]),
            "scheduled": len([p for p in all_posts if p.status == "scheduled"]),
            "published": len(published_posts),
        },
        "engagement_summary": {
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "avg_engagement_rate": "0%" if not published_posts else f"{(total_likes + total_comments + total_shares) / len(published_posts):.1f}%",
        },
        "content_performance": {
            "best_performing_topics": ["AI", "Technology", "Innovation"],
            "optimal_post_length": "Medium",
            "best_posting_days": ["Tuesday", "Wednesday", "Thursday"],
        }
    }


@router.get("/post/{post_id}")
async def get_post_analytics(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific post"""
    
    analytics = db.query(PostAnalytics).filter(
        PostAnalytics.post_id == post_id,
        PostAnalytics.user_id == current_user.id
    ).first()
    
    if not analytics:
        raise HTTPException(status_code=404, detail="No analytics found for this post")
    
    return {
        "post_id": post_id,
        "likes_count": analytics.likes_count,
        "comments_count": analytics.comments_count,
        "shares_count": analytics.shares_count,
        "views_count": analytics.views_count,
        "clicks_count": analytics.clicks_count,
        "engagement_rate": analytics.engagement_rate,
        "reach": analytics.reach,
        "impressions": analytics.impressions,
        "audience_data": analytics.audience_data,
        "top_countries": analytics.top_countries,
        "peak_engagement_time": analytics.peak_engagement_time,
        "metrics_history": analytics.metrics_history,
        "last_updated": analytics.last_updated
    }

@router.post("/update/{post_id}")
async def update_post_analytics(
    post_id: int,
    analytics_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update analytics for a specific post (manual or from LinkedIn API)"""
    
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Update or create analytics record
    analytics = db.query(PostAnalytics).filter(
        PostAnalytics.post_id == post_id
    ).first()
    
    if analytics:
        # Update existing
        analytics.likes_count = analytics_data.get("likes_count", analytics.likes_count)
        analytics.comments_count = analytics_data.get("comments_count", analytics.comments_count)
        analytics.shares_count = analytics_data.get("shares_count", analytics.shares_count)
        analytics.views_count = analytics_data.get("views_count", analytics.views_count)
        analytics.clicks_count = analytics_data.get("clicks_count", analytics.clicks_count)
        analytics.reach = analytics_data.get("reach", analytics.reach)
        analytics.impressions = analytics_data.get("impressions", analytics.impressions)
        
        # Calculate engagement rate
        total_engagement = analytics.likes_count + analytics.comments_count + analytics.shares_count
        if analytics.impressions > 0:
            engagement_rate = (total_engagement / analytics.impressions) * 100
            analytics.engagement_rate = f"{engagement_rate:.1f}%"
        
        analytics.last_updated = datetime.utcnow()
    else:
        # Create new analytics record
        total_engagement = (
            analytics_data.get("likes_count", 0) + 
            analytics_data.get("comments_count", 0) + 
            analytics_data.get("shares_count", 0)
        )
        impressions = analytics_data.get("impressions", 0)
        engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0
        
        analytics = PostAnalytics(
            user_id=current_user.id,
            post_id=post_id,
            likes_count=analytics_data.get("likes_count", 0),
            comments_count=analytics_data.get("comments_count", 0),
            shares_count=analytics_data.get("shares_count", 0),
            views_count=analytics_data.get("views_count", 0),
            clicks_count=analytics_data.get("clicks_count", 0),
            engagement_rate=f"{engagement_rate:.1f}%",
            reach=analytics_data.get("reach", 0),
            impressions=impressions,
            audience_data=analytics_data.get("audience_data", {}),
            top_countries=analytics_data.get("top_countries", [])
        )
        db.add(analytics)
    
    db.commit()
    db.refresh(analytics)
    
    return {
        "success": True,
        "message": "Analytics updated successfully",
        "analytics": {
            "likes_count": analytics.likes_count,
            "engagement_rate": analytics.engagement_rate,
            "impressions": analytics.impressions
        }
    }

@router.get("/performance-trends")
async def get_performance_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    posts_with_analytics = db.query(Post, PostAnalytics).join(
        PostAnalytics, Post.id == PostAnalytics.post_id
    ).filter(
        Post.user_id == current_user.id,
        Post.published_time >= start_date
    ).order_by(Post.published_time).all()
    
    trends_data = []
    for post, analytics in posts_with_analytics:
        trends_data.append({
            "date": post.published_time.date(),
            "impressions": analytics.impressions,
            "engagement_rate": analytics.engagement_rate,
            "likes": analytics.likes_count,
            "comments": analytics.comments_count,
            "shares": analytics.shares_count,
            "post_type": post.post_type
        })
    
    return {
        "period": f"Last {days} days",
        "data_points": len(trends_data),
        "trends": trends_data
    }
