from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, posts, voice, conversations, messages, analyze_command, execute_command, turtle_execute, google_speech, paraphrase

from app.database.connection import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Py-Talk API",
    description="A FastAPI application with PostgreSQL database",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:5173",  # Docker network communication
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api")
app.include_router(google_speech.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
print("analyze_command router:", analyze_command.router)
app.include_router(analyze_command.router, prefix="/api")
app.include_router(execute_command.router, prefix="/api")
app.include_router(turtle_execute.router, prefix="/api")
app.include_router(paraphrase.router, prefix="/api")


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
