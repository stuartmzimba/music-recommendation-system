"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./music_recommender.db"
    
    # Redis (disabled for SQLite setup)
    REDIS_URL: Optional[str] = None
    
    # Spotify API
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    DEBUG: bool = True
    
    # ML Configuration
    MIN_SUPPORT: float = 0.01
    MIN_CONFIDENCE: float = 0.5
    MAX_RULES: int = 1000
    
    # Recommendation Configuration
    DEFAULT_TOP_K: int = 10
    CACHE_TTL: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
