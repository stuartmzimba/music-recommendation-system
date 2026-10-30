"""
FastAPI main application entry point for the Music Recommender System.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager
import sys
import os

# Ensure project root is in sys.path for absolute imports
# __file__ = backend/app/main.py -> go 3 levels up to Recommendation System/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import your project modules
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.models.database import Song, AssociationRule, UserListeningHistory, PopularSong
from backend.app.api.routes import router as api_router

# Configure logging
log_level = getattr(logging, getattr(settings, "LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Music Recommender API...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down Music Recommender API...")


# Create FastAPI application
app = FastAPI(
    title="Music Recommender API",
    description="A hybrid music recommendation system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount standalone modern web frontend (Apple Music Clean)
frontend_web_dir = os.path.join(PROJECT_ROOT, "frontend_web")
if os.path.isdir(frontend_web_dir):
    app.mount("/app", StaticFiles(directory=frontend_web_dir, html=True), name="frontend_app")


@app.get("/")
async def root(request: Request):
    """
    Root endpoint.
    If requested by a web browser, redirect to the Apple Music web interface (/app/).
    Otherwise, return API version metadata.
    """
    accept = request.headers.get("accept", "")
    user_agent = request.headers.get("user-agent", "")
    if "text/html" in accept and "testclient" not in user_agent.lower():
        return RedirectResponse(url="/app/")
    return {"message": "Music Recommender API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "music-recommender-api"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",  # Matches folder structure
        host=getattr(settings, "API_HOST", "127.0.0.1"),
        port=getattr(settings, "API_PORT", 8001),
        reload=getattr(settings, "DEBUG", True),
    )


