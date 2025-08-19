# backend/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .database import get_db
from .api import users  # Import user routes
from sqlalchemy.orm import Session
from sqlalchemy import text
from .api import content
from .api import linkedin_integration
from .api.analytics import router as analytics_router
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LinkedIn AI Agent API",
    description="AI-powered LinkedIn content generation and automation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(content.router)
app.include_router(linkedin_integration.router)
app.include_router(analytics_router)


@app.get("/")
async def root():
    env = os.getenv("ENVIRONMENT", "unknown")
    return {
        "message": "LinkedIn AI Agent", 
        "environment": env,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "linkedin-ai-agent"}

@app.get("/db-test")
async def test_database_connection(db: Session = Depends(get_db)):
    """Test database connection and show PostgreSQL version"""
    try:
        result = db.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        
        return {
            "status": "Database connected successfully!",
            "postgres_version": version
        }
    except Exception as e:
        return {
            "status": "Database connection failed",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
