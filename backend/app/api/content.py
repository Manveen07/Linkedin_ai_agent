# backend/app/api/content.py



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.post import Post
from ..services.gemini_content_service import GeminiContentService
from ..api.users import get_current_user
from datetime import datetime
from ..models.post import Post

router = APIRouter(prefix="/api/content", tags=["content"])
ai_service = GeminiContentService()

class ContentGenerationRequest(BaseModel):
    topic: str
    post_type: str = "professional"  # professional, casual, thought_leadership
    length: str = "medium"  # short, medium, long
    industry: Optional[str] = None
    tone: Optional[str] = "professional"
    audience: Optional[str] = None
    max_characters: int = 3000 

class SaveDraftRequest(BaseModel):
    content: str
    hashtags: List[str]
    topic: str

class GeneratedContentResponse(BaseModel):
    content: str
    hashtags: List[str]
    mentions: List[str]
    post_type: str
    ai_model: str
    topic: str
    estimated_engagement: dict
    character_count: Optional[int] = None
    post_id: int  


# @router.post("/generate", response_model=GeneratedContentResponse)
# async def generate_content(
#     request: ContentGenerationRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Generate AI-powered LinkedIn content using Google Gemini"""
    
#     result = await ai_service.generate_linkedin_post(
#         user=current_user,
#         topic=request.topic,
#         post_type=request.post_type,
#         length=request.length,
#         tone=request.tone,
#         audience=request.audience
#     )

#     
#     if "error" in result:
#         raise HTTPException(status_code=500, detail=result["error"])
    
#     # Create and save Post object to database
#     new_post = Post(
#         user_id=current_user.id,
#         content=result['content'],
#         hashtags=result.get('hashtags', []),
#         post_type=request.post_type,
#         status="generated",
#         ai_prompt_used=f"Topic: {request.topic}, Type: {request.post_type}, Tone: {request.tone}",
#         generation_model="gemini",
#         topics_used=[request.topic],
#         predicted_engagement=result.get('estimated_engagement', {})
#     )
    
#     db.add(new_post)
#     db.commit()
#     db.refresh(new_post)
    
#     # Add character count
#     result['character_count'] = len(result['content'])
#     result["post_id"] = new_post.id
    
#     return result

def calculate_character_limit_status(content: str, hashtags: list[str], max_characters: int = 3000):
    """
    Check if LinkedIn post content + hashtags stay within the character limit.
    - LinkedIn hard limit = 3000
    - Soft safe limit ~ 2700 (prevents cutoff issues)
    
    Returns:
        (status, soft_limit, total_chars)
    """
    hashtags_text = " ".join([f"#{tag}" for tag in hashtags])
    total_chars = len(content) + (1 if hashtags_text else 0) + len(hashtags_text)

    # Soft limit = 90% of max
    soft_limit = int(max_characters * 0.9)

    if total_chars <= soft_limit:
        return "within_limit", soft_limit, total_chars
    elif total_chars <= max_characters:
        return "near_limit", soft_limit, total_chars
    else:
        return "exceeds_limit", soft_limit, total_chars

import re

def trim_content_to_limit(content: str, hashtags: list[str], max_characters: int = 3000):
    """
    Smart trim for LinkedIn content + hashtags:
    - Prefer trimming at sentence boundaries (., !, ?)
    - If no sentence break, trim at word boundary
    - Finally, enforce hard cut if needed
    - Ensures final string <= max_characters
    """
    hashtags_text = " ".join([f"#{tag}" for tag in hashtags])
    combined = f"{content} {hashtags_text}".strip()

    if len(combined) <= max_characters:
        return content, hashtags

    # --- Step 1: Reserve space for hashtags ---
    allowed_len = max_characters - len(hashtags_text) - 1
    if allowed_len > 0:
        if len(content) > allowed_len:
            truncated = content[:allowed_len]

            # --- Step 2: Try cutting at last sentence boundary ---
            sentence_cut = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
            if sentence_cut != -1 and sentence_cut > allowed_len * 0.6:  
                content = truncated[:sentence_cut+1]
            else:
                # --- Step 3: Try cutting at word boundary ---
                word_cut = truncated.rfind(" ")
                if word_cut != -1 and word_cut > allowed_len * 0.6:
                    content = truncated[:word_cut]
                else:
                    # --- Step 4: Fallback: hard cut ---
                    content = truncated.rstrip()

        combined = f"{content} {hashtags_text}".strip()

    # --- Step 5: If still too long, trim hashtags progressively ---
    if len(combined) > max_characters:
        while hashtags and len(combined) > max_characters:
            hashtags.pop()
            hashtags_text = " ".join([f"#{tag}" for tag in hashtags])
            combined = f"{content} {hashtags_text}".strip()

    return content.strip(), hashtags


@router.post("/generate", response_model=GeneratedContentResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered LinkedIn content using Google Gemini with strict character enforcement"""
    
    warnings = []
    max_chars = getattr(request, "max_characters", None) or 3000

    # Step 0: Ask Gemini to generate content
    result = await ai_service.generate_linkedin_post(
        user=current_user,
        topic=request.topic,
        post_type=request.post_type,
        length=request.length,
        tone=request.tone,
        audience=request.audience
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    content = result.get("content", "")
    hashtags = result.get("hashtags", [])
    engagement = result.get("estimated_engagement", {})

    # Step 1: Evaluate initial response
    status, _, total_chars = calculate_character_limit_status(content, hashtags, max_chars)

    # Step 2: Retry with stricter AI prompt if needed
    if status == "exceeds_limit":
        retry_prompt = (
            f"Rewrite this LinkedIn post as a detailed long-form LinkedIn article. "
            f"Target between {int(max_chars*0.9)} and {max_chars} characters "
            f"(including spaces). Do not go below {int(max_chars*0.85)} characters. "
            f"Keep all key ideas, expand explanations, and ensure readability:\n\n{content}"
        )
        retry_result = await ai_service.generate_content(retry_prompt)
        retry_content = retry_result.get("content", "")
        retry_status, _, retry_chars = calculate_character_limit_status(retry_content, hashtags, max_chars)

        if retry_status in ["within_limit", "near_limit"]:
            content = retry_content
            total_chars = retry_chars
            warnings.append(
                f"First attempt exceeded character limit → AI rewrite applied "
                f"(final length: {total_chars})"
            )
        else:
            content, hashtags = trim_content_to_limit(content, hashtags, max_chars)
            _, _, total_chars = calculate_character_limit_status(content, hashtags, max_chars)
            warnings.append("Fallback trimming applied to enforce character limit")



    # Step 4: Save to DB
    new_post = Post(
        user_id=current_user.id,
        content=content,
        hashtags=hashtags,
        post_type=request.post_type,
        status="generated",
        ai_prompt_used=f"Topic: {request.topic}, Type: {request.post_type}, Tone: {request.tone}",
        generation_model="gemini",
        topics_used=[request.topic],
        predicted_engagement=engagement
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Step 5: Final response
    return {
        "content": content,
        "hashtags": hashtags,
        "mentions": [],  # later you can parse from content
        "post_type": request.post_type,
        "ai_model": "gemini-1.5-flash",
        "topic": request.topic,
        "estimated_engagement": engagement,
        "character_count": total_chars,
        "status": "success",
        "warnings": warnings,
        "post_id": new_post.id
    }



@router.post("/generate-variations")
async def generate_content_variations(
    topic: str,
    current_user: User = Depends(get_current_user)
):
    """Generate multiple content variations for A/B testing"""
    
    variations = ai_service.generate_multiple_variations(current_user, topic, count=3)
    
    return {
        "topic": topic,
        "variations": variations,
        "total": len(variations)
    }

@router.post("/save-draft")
async def save_draft(
    request: SaveDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save generated content as draft"""
    
    draft_post = Post(
        user_id=current_user.id,
        content=request.content,
        hashtags=request.hashtags,
        status="draft",
        ai_prompt_used=request.topic,
        generation_model="gemini-1.5-flash"
    )
    
    db.add(draft_post)
    db.commit()
    db.refresh(draft_post)
    
    return {
        "message": "Draft saved successfully",
        "post_id": draft_post.id,
        "status": "draft"
    }

@router.get("/drafts")
async def get_user_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all drafts for current user"""
    
    drafts = db.query(Post).filter(
        Post.user_id == current_user.id,
        Post.status == "draft"
    ).order_by(Post.created_at.desc()).all()
    
    return {
        "drafts": drafts,
        "total": len(drafts)
    }

@router.get("/suggestions/{industry}")
async def get_topic_suggestions(industry: str):
    """Get AI-generated trending topic suggestions for industry"""
    
    try:
        # Use your existing AI service to generate suggestions
        ai_prompt = f"""
        Generate 5 trending and engaging LinkedIn post topics for the {industry} industry.
        Focus on current trends, professional insights, and content that would drive engagement.
        Return only the topic titles, one per line.
        """
        
        # Call your AI service (assuming you have GeminiContentService or similar)
        
        ai_response = await ai_service.generate_content(ai_prompt)
        
        # Parse the AI response into a list of suggestions
        if ai_response and 'content' in ai_response:
            suggestions_text = ai_response['content']
            suggestions_list = [
                line.strip() 
                for line in suggestions_text.split('\n') 
                if line.strip() and not line.strip().startswith('-')
            ][:5]  # Limit to 5 suggestions
        else:
            # Fallback to hardcoded if AI fails
            suggestions_list = get_fallback_suggestions(industry)
        
    except Exception as e:
        print(f"AI suggestion generation failed: {e}")
        # Fallback to hardcoded suggestions
        suggestions_list = get_fallback_suggestions(industry)
    
    return {
        "industry": industry,
        "suggestions": suggestions_list
    }

def get_fallback_suggestions(industry: str):
    """Fallback hardcoded suggestions if AI fails"""
    fallback_suggestions = {
        "Technology": [
            "AI and Machine Learning trends",
            "Remote work productivity",
            "Digital transformation",
            "Cybersecurity best practices",
            "Future of software development"
        ],
        "Marketing": [
            "Social media marketing trends",
            "Content marketing strategies",
            "Customer experience optimization",
            "Brand storytelling",
            "Digital marketing analytics"
        ],
        "Finance": [
            "Fintech innovations",
            "Investment strategies",
            "Cryptocurrency trends",
            "Financial planning tips",
            "Economic market analysis"
        ],
        "Healthcare": [
            "Digital health innovations",
            "Patient care optimization",
            "Healthcare technology trends",
            "Medical research insights",
            "Healthcare policy updates"
        ],
        "Education": [
            "EdTech innovations",
            "Online learning trends",
            "Student engagement strategies",
            "Educational technology",
            "Future of education"
        ]
    }
    
    return fallback_suggestions.get(industry, fallback_suggestions["Technology"])



class SchedulePostRequest(BaseModel):
    post_id: int
    scheduled_time: datetime

@router.post("/schedule-post")
async def schedule_post(
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter_by(id=request.post_id, user_id=current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.scheduled_time = request.scheduled_time
    post.status = "scheduled"
    db.commit()
    db.refresh(post)
    
    return {
        "success": True,
        "message": "Post scheduled",
        "post_id": post.id,
        "scheduled_time": post.scheduled_time
    }

# Add this new Pydantic model
class ContentSuggestionRequest(BaseModel):
    current_content: str
    suggestion_type: str = "improve"  # improve, shorten, expand, tone_change, custom
    target_tone: Optional[str] = None
    specific_request: Optional[str] = None
    max_characters: Optional[int] = 3000


class ContentSuggestionResponse(BaseModel):
    suggestions: List[str]
    suggestion_type: str
    original_length: int
    suggested_lengths: List[int]




@router.post("/improve", response_model=GeneratedContentResponse)
async def improve_content(
    request: ContentSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rewrite LinkedIn content by applying improvements directly with character limit enforcement"""
    
    warnings = []
    max_chars = getattr(request, "max_characters", None) or 3000

    # Step 0: Build AI prompt depending on suggestion type
    if request.suggestion_type == "improve":
        ai_prompt = f"""
        Rewrite the following LinkedIn post by applying improvements directly.

        Current post:
        {request.current_content}

        Apply improvements for:
        - Stronger engagement (hooks, CTAs, questions)
        - Clearer and more professional tone
        - Better structure and readability

        Return ONE improved post only, not suggestions or lists.
        """

    elif request.suggestion_type == "shorten":
        ai_prompt = f"""
        Rewrite the following LinkedIn post into ONE concise version about 50% shorter,
        while keeping the core message intact.

        Original post:
        {request.current_content}
        """

    elif request.suggestion_type == "expand":
        ai_prompt = f"""
        Expand the following LinkedIn post into ONE version under {max_chars} characters.

        Current post:
        {request.current_content}

        Add:
        - More examples and details
        - Industry insights or trends
        - A touch of personal experience

        Return ONE rewritten post only.
        """

    elif request.suggestion_type == "tone_change":
        target_tone = request.target_tone or "professional"
        ai_prompt = f"""
        Rewrite the following LinkedIn post in a {target_tone} tone.

        Original post:
        {request.current_content}

        Return ONE rewritten post only.
        """

    elif request.suggestion_type == "custom":
        ai_prompt = f"""
        Modify the following LinkedIn post based on this request: "{request.specific_request}"

        Current post:
        {request.current_content}

        Return ONE rewritten post only.
        """
    else:
        raise HTTPException(status_code=400, detail="Invalid suggestion type")

    # Step 1: Ask Gemini to rewrite
    result = await ai_service.generate_content(ai_prompt)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    content = result.get("content", "").strip()
    hashtags = result.get("hashtags", [])
    engagement = result.get("estimated_engagement", {})

    # Step 2: Enforce character limit (like /generate)
    status, _, total_chars = calculate_character_limit_status(content, hashtags, max_chars)

    if status == "exceeds_limit":
        retry_prompt = (
            f"Rewrite this LinkedIn post to stay within {max_chars} characters. "
            f"Do not drop the main ideas, just make it concise:\n\n{content}"
        )
        retry_result = await ai_service.generate_content(retry_prompt)
        retry_content = retry_result.get("content", "").strip()
        retry_status, _, retry_chars = calculate_character_limit_status(retry_content, hashtags, max_chars)

        if retry_status in ["within_limit", "near_limit"]:
            content = retry_content
            total_chars = retry_chars
            warnings.append(
                f"First attempt exceeded character limit → AI rewrite applied "
                f"(final length: {total_chars})"
            )
        else:
            content, hashtags = trim_content_to_limit(content, hashtags, max_chars)
            _, _, total_chars = calculate_character_limit_status(content, hashtags, max_chars)
            warnings.append("Fallback trimming applied to enforce character limit")

    # Step 3: Save improved post to DB
    new_post = Post(
        user_id=current_user.id,
        content=content,
        hashtags=hashtags,
        post_type="improved",  # distinguish from generated
        status="improved",
        ai_prompt_used=f"Suggestion type: {request.suggestion_type}",
        generation_model="gemini",
        topics_used=[],
        predicted_engagement=engagement
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Step 4: Final structured response
    return {
        "content": content,
        "hashtags": hashtags,
        "mentions": [],
        "post_type": "improved",
        "ai_model": "gemini-1.5-flash",
        "topic": "",
        "estimated_engagement": engagement,
        "character_count": total_chars,
        "status": "success",
        "warnings": warnings,
        "post_id": new_post.id
    }
