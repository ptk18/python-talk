import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.common import auth, users, posts, messages, translate, paraphrase, favorites
from app.routers.codespace import analyze_command, execute_command, conversations
from app.routers.turtle import turtle_commands, turtle_execute
from app.routers.voice import voice, google_speech
from app.nlp_v4 import preload_models
from app.database.connection import engine, Base

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    prewarm_enabled = os.getenv("PREWARM_MODELS", "true").lower() == "true"

    if prewarm_enabled:
        print("\n🚀 Starting model pre-warming in background...")
        def prewarm_background():
            try:
                voice.prewarm_models()
            except Exception as e:
                print(f"Voice model pre-warming failed: {e}")

            try:
                preload_models()
            except Exception as e:
                print(f"NLP model pre-warming failed: {e}")

        thread = threading.Thread(target=prewarm_background, daemon=True)
        thread.start()
    else:
        print("\n⏭️ Model pre-warming disabled (set PREWARM_MODELS=true to enable)")

    yield  

    print("\nShutting down Py-Talk API...")

app = FastAPI(
    title="Py-Talk API",
    description="A FastAPI application with PostgreSQL database",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api")
app.include_router(google_speech.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(analyze_command.router, prefix="/api")
app.include_router(execute_command.router, prefix="/api")
app.include_router(turtle_execute.router, prefix="/api")
app.include_router(paraphrase.router, prefix="/api")
app.include_router(translate.router, prefix="/api")
app.include_router(turtle_commands.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Py-Talk API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
