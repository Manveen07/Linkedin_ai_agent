# backend/app/api/linkedin_integration.py
from app.models.analytics import PostAnalytics
from ..models.post import Post
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..api.users import get_current_user
from ..services.linkedin_oauth_service import LinkedInOAuthService
from ..services.linkedin_publisher import LinkedInPublisher
from pydantic import BaseModel
from datetime import datetime

import os

router = APIRouter(prefix="/api/linkedin", tags=["linkedin"])
oauth_service = LinkedInOAuthService()
publisher = LinkedInPublisher()

class PublishRequest(BaseModel):
    content: str

class ExchangeTokenRequest(BaseModel):
    code: str

# In backend/app/api/linkedin_integration.py
@router.get("/connect")
async def connect_linkedin(current_user: User = Depends(get_current_user)):
    """Start LinkedIn OAuth flow"""
    
    # Debug: Check if environment variables are loaded
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="LinkedIn Client ID not configured")
    
    oauth_service = LinkedInOAuthService()
    auth_url = oauth_service.get_authorization_url()
    
    return {
        "authorization_url": auth_url,
        "message": "Visit this URL to connect your LinkedIn account"
    }

# @router.get("/callback")
# async def linkedin_callback(code: str = None, state: str = None, error: str = None):
#     """Handle LinkedIn OAuth callback"""
    
#     if error:
#         raise HTTPException(status_code=400, detail=f"LinkedIn auth error: {error}")
    
#     if not code:
#         raise HTTPException(status_code=400, detail="Authorization code not provided")
    
#     oauth_service = LinkedInOAuthService()
    
#     # Remove 'await' since the method is synchronous
#     token_result = oauth_service.exchange_code_for_token(code)
    
#     if "error" in token_result:
#         raise HTTPException(status_code=400, detail=f"LinkedIn auth error: {token_result['error']}")
    
#     # Process successful token exchange
#     access_token = token_result.get("access_token")
    
#     return {
#         "message": "LinkedIn connected successfully",
#         "access_token": access_token[:10] + "..." if access_token else None  # Truncated for security
#     }


class PublishRequest(BaseModel):
    post_id: int
    content: str


@router.post("/publish")
async def publish_to_linkedin(
    request: PublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish content to LinkedIn"""
    
    # 1. Check LinkedIn connection
    if not current_user.access_token:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn not connected. Please connect your LinkedIn account first."
        )

    person_urn = f"urn:li:person:{current_user.linkedin_id}"

    # 2. Publish to LinkedIn (AI/LinkedIn logic)
    result = await publisher.publish_post(
        access_token=current_user.access_token,
        person_urn=person_urn,
        content=request.content
    )

    # 3. If LinkedIn publish succeeded, update local post and create analytics
    if result.get("success"):
        post = db.query(Post).filter_by(id=request.post_id, user_id=current_user.id).first()
        if post:
            post.status = "published"
            post.published_time = datetime.utcnow()
            # Optionally, save LinkedIn URL/ID if result contains it
            post.linkedin_url = result.get("post_url")
            db.commit()
            db.refresh(post)

            # Create initial analytics record if not present
            if not post.analytics:
                analytics = PostAnalytics(
                    user_id=current_user.id,
                    post_id=post.id,
                    likes_count=0,
                    comments_count=0,
                    shares_count=0,
                    views_count=0,
                    clicks_count=0,
                    engagement_rate="0%",
                    reach=0,
                    impressions=0,
                )
                db.add(analytics)
                db.commit()

    return result



@router.get("/status")
async def linkedin_connection_status(current_user: User = Depends(get_current_user)):
    """Check LinkedIn connection status"""
    
    # Use the linkedin_connected boolean field
    is_connected = current_user.linkedin_connected and bool(current_user.access_token)
    
    return {
        "connected": is_connected,
        "linkedin_id": current_user.linkedin_id if is_connected else None,
        "message": "LinkedIn connected" if is_connected else "LinkedIn not connected"
    }



@router.get("/debug")
async def debug_linkedin_config():
    """Debug endpoint to check LinkedIn configuration"""
    return {
        "client_id_loaded": bool(os.getenv("LINKEDIN_CLIENT_ID")),
        "client_secret_loaded": bool(os.getenv("LINKEDIN_CLIENT_SECRET")),
        "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI")
    }





@router.post("/exchange-token")
async def exchange_linkedin_token(
    request: ExchangeTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange LinkedIn authorization code for access token and save profile"""
    
    try:
        oauth_service = LinkedInOAuthService()
        
        # Get access token
        token_result = oauth_service.exchange_code_for_token(request.code)
        if "error" in token_result:
            raise HTTPException(status_code=400, detail=token_result["error"])
        
        access_token = token_result.get("access_token")
        
        # Fetch LinkedIn profile
        profile_data = oauth_service.get_linkedin_profile(access_token)
        if "error" in profile_data:
            raise HTTPException(status_code=400, detail=profile_data["error"])
        
        # Save profile data selectively to your existing User model
        current_user.linkedin_id = profile_data.get("sub")
        current_user.email = profile_data.get("email", current_user.email)
        current_user.name = profile_data.get("name", current_user.name)
        
        # Only update headline and industry if they exist in LinkedIn profile data
        linkedin_headline = profile_data.get("headline")
        if linkedin_headline and linkedin_headline.strip():
            current_user.headline = linkedin_headline
        
        linkedin_industry = profile_data.get("industry")
        if linkedin_industry and linkedin_industry.strip():
            current_user.industry = linkedin_industry
        
        current_user.location = profile_data.get("location", current_user.location)
        
        # OAuth fields
        current_user.access_token = access_token
        current_user.linkedin_connected = True
        
        from datetime import datetime, timedelta
        current_user.token_expiry = datetime.utcnow() + timedelta(days=60)
        
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": "LinkedIn connected and profile synced",
            "profile": {
                "name": current_user.name,
                "headline": current_user.headline,
                "industry": current_user.industry
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/disconnect")
async def disconnect_linkedin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect LinkedIn from the user's profile"""
    current_user.linkedin_connected = False
    current_user.access_token = None
    current_user.token_expiry = None
    current_user.linkedin_id = None
    # Optionally clear other LinkedIn-specific profile fields if you want strict privacy

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "LinkedIn disconnected successfully"
    }
