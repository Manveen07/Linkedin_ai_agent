import google.generativeai as genai
import os
import re
import time
import random
import asyncio
import logging
from functools import lru_cache
from typing import List, Dict, Optional
from ..models.user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeminiContentService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_content(self, prompt: str) -> dict:
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return {"content": response.text.strip()}
        except Exception as e:
            logger.error(f"Gemini content generation failed: {e}")
            return {"error": str(e), "content": ""}
        

    async def generate_linkedin_post(
        self,
        user: User,
        topic: str,
        post_type: str = "professional",
        length: str = "medium",
        tone: Optional[str] = "professional",
        audience: Optional[str] = None
    ) -> Dict:
        prompt = self._create_prompt(user, topic, post_type, length, tone, audience)
        try:
            response = await asyncio.to_thread(
                self._retry_request,
                self.model.generate_content,
                prompt
            )
            content = response.text.strip()
            hashtags = self._extract_hashtags(content)
            mentions = self._extract_mentions(content)
            return {
                "content": content,
                "hashtags": hashtags,
                "mentions": mentions,
                "post_type": post_type,
                "ai_model": "gemini-1.5-flash",
                "topic": topic,
                "estimated_engagement": self._predict_engagement(content, user, tone, audience)
            }
        except Exception as e:
            logger.error(f"Gemini post generation failed: {e}")
            return {
                "error": f"AI content generation failed: {str(e)}",
                "content": self._fallback_content(topic, user)
            }

    async def generate_multiple_variations(self, user: User, topic: str, count: int = 3) -> List[Dict]:
        tasks = []
        post_types = ["professional", "casual", "thought_leadership"]
        tones = ["professional", "casual", "inspirational"]

        for i in range(count):
            post_type = post_types[i % len(post_types)]
            tone = tones[i % len(tones)]
            tasks.append(self.generate_linkedin_post(user, topic, post_type, tone=tone))

        return await asyncio.gather(*tasks)

    def _retry_request(self, func, *args, retries=3, delay=2, **kwargs):
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                sleep_time = delay * (2 ** attempt) + random.random()
                logger.warning(f"Retry {attempt+1}/{retries} after error: {e}. Sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

    def _extract_hashtags(self, content: str) -> List[str]:
        hashtags = re.findall(r'#\w[\w-]*', content)
        return [tag.lower() for tag in hashtags]

    def _extract_mentions(self, content: str) -> List[str]:
        mentions = re.findall(r'@[A-Za-z0-9_.-]+', content)
        return mentions

    def _predict_engagement(
        self,
        content: str,
        user: User,
        tone: Optional[str] = "professional",
        audience: Optional[str] = None
    ) -> Dict:
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        hashtag_count = len(self._extract_hashtags(content))

        has_question = "?" in content
        has_cta = any(cta in content.lower() for cta in [
            "what do you think", "share your", "let me know", "comment below",
            "thoughts?", "agree?", "disagree?", "experience?", "what's your"
        ])
        has_story = any(story in content.lower() for story in [
            "recently", "yesterday", "last week", "remember when", "story", "experience"
        ])
        has_data = any(keyword in content.lower() for keyword in [
            "%", "$", "study", "research", "data", "report"
        ])

        base_score = 45
        if has_question: base_score += 20
        if has_cta: base_score += 15
        if has_story: base_score += 18
        if has_data: base_score += 12
        if 3 <= hashtag_count <= 5: base_score += 8
        if 100 <= word_count <= 200: base_score += 10
        if sentence_count >= 3: base_score += 5

        tone_multipliers = {"casual": 1.25, "inspirational": 1.35, "professional": 1.0}
        audience_multipliers = {"entry": 1.1, "manager": 1.2, "executive": 1.15, "all": 1.0}

        base_score *= tone_multipliers.get(tone, 1.0)
        base_score *= audience_multipliers.get(audience, 1.0)
        if user.industry in ["Technology", "Marketing"]:
            base_score *= 1.1

        final_score = min(int(base_score), 95)
        return {
            "predicted_likes": min(final_score * 3, 300),
            "predicted_comments": min(final_score // 3, 35),
            "predicted_shares": min(final_score // 8, 15),
            "engagement_score": final_score
        }

    def _fallback_content(self, topic: str, user: User) -> str:
        industry = user.industry or "professional"
        role = user.current_role or "professional"
        templates = [
            f"Sharing insights on {topic} in the {industry} space. What’s your perspective?",
            f"As a {role}, I’ve been reflecting on {topic}. Curious how others see it?",
            f"Excited to explore how {topic} is shaping {industry}. Drop your thoughts below!"
        ]
        return random.choice(templates) + f" #{industry.lower().replace(' ', '')} #innovation #thoughtleadership"

#     def _create_prompt(
#         self,
#         user: User,
#         topic: str,
#         post_type: str,
#         length: str,
#         tone: Optional[str] = "professional",
#         audience: Optional[str] = None
#     ) -> str:
#         industry_context = self._get_industry_context(user.industry)
#         trend_context = self._get_trending_topics(user.industry)
#         structure_guide = self._get_content_structure(post_type, length)
#         prompt = f"""
# You are an expert LinkedIn content strategist specializing in {user.industry or 'Technology'} industry content.

# CREATE A HIGH-ENGAGEMENT LINKEDIN POST:

# USER PROFILE:
# - Professional: {user.current_role or 'Professional'} at {user.company or 'Company'}
# - Industry: {user.industry or 'Technology'}
# - Brand Voice: {user.brand_voice or 'Professional and authoritative'}
# - Expertise Level: Senior professional with industry credibility

# CONTENT REQUIREMENTS:
# Topic: {topic}
# Style: {post_type}
# Tone: {tone}
# Target Audience: {audience or 'Industry professionals'}
# Length: {structure_guide['length_instruction']} (DO NOT exceed 220 words)

# INDUSTRY CONTEXT:
# {industry_context}

# CURRENT TRENDS TO INCORPORATE:
# {trend_context}

# CONTENT STRUCTURE:
# {structure_guide['structure']}

# ENGAGEMENT OPTIMIZATION:
# 1. Start with a compelling hook
# 2. Include personal insights or experiences
# 3. Add industry-specific data or statistics
# 4. Use storytelling elements appropriate for {tone} tone
# 5. Include a thought-provoking question or CTA
# 6. Add 3-5 relevant hashtags
# 7. Ensure content demonstrates expertise in {user.industry}

# OUTPUT FORMAT:
# Return ONLY the LinkedIn post content, plain text, with line breaks. No markdown.
# """
#         return prompt
 

    def _create_prompt(self, user: User, topic: str, post_type: str, length: str, tone: str, audience: str):
        # Use real LinkedIn profile data for personalization
        user_context = f"""
USER PROFILE FROM LINKEDIN:
- Name: {user.name}
- Professional Headline: {user.headline or 'Professional'}
- Industry: {user.industry or 'Technology'}
- Current Role: {user.current_role or 'Professional'}
- Company: {user.company or 'Current Company'}
- Location: {user.location or 'Global'}
- Brand Voice: {user.brand_voice}
- Skills: {', '.join(user.skills[:5]) if user.skills else 'Various professional skills'}
"""

        prompt = f"""
You are creating content for {user.name}, a real LinkedIn professional.

{user_context}

CREATE A HIGH-ENGAGEMENT LINKEDIN POST:
Topic: {topic}
Style: {post_type}
Tone: {tone}
Target Audience: {audience or 'Industry professionals'}

Make this post authentic to {user.name}'s professional background in {user.industry}.
Reference their expertise and use language that matches their {user.brand_voice} brand voice.

{self._get_industry_context(user.industry)}
{self._get_content_structure(post_type, length)['structure']}
"""
        return prompt

    def _get_industry_context(self, industry: str) -> str:
        industry_contexts = {
            "Technology": """Focus: AI/ML, digital transformation, cybersecurity, startups.
Key themes: Disruption, scalability, UX, data-driven decisions, emerging tech.
Audience: Future-focused, practical insights, credible commentary.""",
            "Marketing": """Focus: Digital strategies, branding, automation, ROI.
Key themes: Customer journey, personalization, omnichannel, storytelling.
Audience: Actionable tactics, case studies, performance metrics.""",
            "Finance": """Focus: Investment, fintech, regulation, trends.
Key themes: Market volatility, diversification, digital banking, crypto.
Audience: Data-backed insights, predictions, compliance updates.""",
            "Healthcare": """Focus: Digital health, telemedicine, patient care, policy.
Key themes: Outcomes, accessibility, innovation, compliance, prevention.
Audience: Evidence-based, safety-focused, tech adoption insights.""",
            "Education": """Focus: EdTech, learning methods, online education.
Key themes: Personalized learning, accessibility, skills development.
Audience: Pedagogical insights, tech integration, student success stories."""
        }
        return industry_contexts.get(industry, industry_contexts["Technology"])

    @lru_cache(maxsize=10)
    def _get_trending_topics(self, industry: str) -> str:
        trending_topics = {
            "Technology": "AI automation, remote work tools, cybersecurity threats, sustainable tech, quantum computing",
            "Marketing": "AI personalization, privacy-first marketing, influencer partnerships, video content, social commerce",
            "Finance": "Digital banking, ESG investing, crypto adoption, fintech regulation, financial wellness",
            "Healthcare": "Telemedicine, AI diagnostics, patient data security, mental health, preventive care",
            "Education": "Hybrid models, AI tutoring, skills-based learning, educational equity, micro-credentials"
        }
        return f"Current trending topics in {industry}: {trending_topics.get(industry, trending_topics['Technology'])}"

    def _get_content_structure(self, post_type: str, length: str) -> Dict:
        structures = {
            "professional": {
                "short": {
                    "length_instruction": "50-100 words, concise and impactful",
                    "structure": """1. Strong opening
2. Key insight or data
3. Brief perspective
4. Call-to-action"""
                },
                "medium": {
                    "length_instruction": "100-200 words, balanced depth and engagement",
                    "structure": """1. Attention hook
2. Context (2-3 sentences)
3. Main insight with support
4. Personal example
5. Engaging CTA"""
                },
                "long": {
                    "length_instruction": "200-300 words, comprehensive storytelling",
                    "structure": """1. Story opener
2. Background context
3. Detailed analysis
4. Case study
5. Takeaways
6. CTA"""
                }
            },
            "casual": {
                "short": {
                    "length_instruction": "50-100 words, conversational",
                    "structure": """1. Personal anecdote
2. Relatable insight
3. Light humor
4. Question"""
                },
                "medium": {
                    "length_instruction": "100-200 words, conversational and relatable",
                    "structure": """1. Casual opener
2. Relevant story
3. Lesson or insight
4. Friendly CTA"""
                },
                "long": {
                    "length_instruction": "200-300 words, informal storytelling",
                    "structure": """1. Story-driven intro
2. Detailed narrative
3. Relatable lesson
4. Sign-off + question"""
                }
            },
            "thought_leadership": {
                "short": {
                    "length_instruction": "50-100 words, authoritative",
                    "structure": """1. Bold view
2. Supporting rationale
3. Implication
4. Starter question"""
                },
                "medium": {
                    "length_instruction": "100-200 words, insightful",
                    "structure": """1. Trend/challenge
2. Unique perspective
3. Evidence
4. Question for leaders"""
                },
                "long": {
                    "length_instruction": "200-300 words, broad analysis",
                    "structure": """1. Strategic observation
2. Evaluation
3. Bold stance
4. Future vision + CTA"""
                }
            }
        }
        return structures.get(post_type, structures["professional"]).get(
            length, structures["professional"]["medium"]
        )
