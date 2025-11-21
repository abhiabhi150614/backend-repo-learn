from fastapi import FastAPI,Response
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, onboarding, youtube_schedule, chatbot, call_bot, voice_webhook, recruiter
from app.routes import learning_plan, subplans
from app.routes import quiz
from app.database.db import create_tables, engine, Base
from sqlalchemy import text
import os

app = FastAPI(title="EduAI Learning Platform", version="1.0.0")

# Configure CORS - Allow both local and production frontends
allowed_origins = [
    "https://abhishekbabushetty-ccbp.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add production frontend URL from environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(onboarding.router, tags=["Onboarding"])
app.include_router(youtube_schedule.router, tags=["YouTubeSchedule"])
app.include_router(chatbot.router, tags=["Chatbot"])
app.include_router(call_bot.router, prefix="/call", tags=["CallBot"])
app.include_router(voice_webhook.router, tags=["VoiceWebhook"])
app.include_router(learning_plan.router, tags=["LearningPlan"])
app.include_router(subplans.router, tags=["Subplans"])
app.include_router(quiz.router, tags=["Quiz"])
app.include_router(recruiter.router, tags=["Recruiter"])

@app.on_event("startup")
async def startup_event():
    """Fresh database setup: drop and recreate all tables on startup"""
    try:
        print("🔄 Fresh database setup - dropping and recreating all tables...")
        
        # Import all models to ensure they're registered
        from app.models import user, onboarding, learning_plan, job, email_application, candidate_vector, quiz, shortlist
        
        # Drop all tables and recreate them fresh
        print("🗑️ Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
        
        print("🔨 Creating all tables fresh...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created fresh")
        
    except Exception as e:
        print(f"❌ Error during table creation: {e}")



@app.get("/")
def read_root():
    return {"message": "EduAI Learning Platform API"}

@app.get("/health")
def health_check(response: Response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return {"status": "alive for ever"}
