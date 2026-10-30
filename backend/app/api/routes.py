"""
API routes for the Music Recommender System.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.app.core.database import get_db
from backend.app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    PopularSongsResponse,
    SongSearchResult,
    SystemStatsResponse
)
from backend.app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recommend", response_model=List[RecommendationResponse])
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get personalized music recommendations.
    
    Hybrid approach:
    1. Apriori algorithm for association rules
    2. Content-based filtering as fallback
    3. Popular songs as final fallback
    """
    try:
        service = RecommendationService(db)
        recommendations = await service.get_recommendations(
            basket=request.basket,
            genres=request.genres,
            user_id=request.user_id,
            top_k=request.top_k
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.get("/popular", response_model=List[PopularSongsResponse])
async def get_popular_songs(
    limit: int = 20,
    genre: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get popular songs in South Africa.

    Args:
        limit: Number of songs to return
        genre: Optional genre filter
    """
    try:
        service = RecommendationService(db)
        popular_songs = await service.get_popular_songs(limit=limit, genre=genre)
        return popular_songs
    except Exception as e:
        logger.error(f"Error getting popular songs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular songs"
        )


@router.get("/genres")
async def get_available_genres(db: Session = Depends(get_db)):
    """Get list of available genres."""
    try:
        service = RecommendationService(db)
        genres = await service.get_available_genres()
        return {"genres": genres}
    except Exception as e:
        logger.error(f"Error getting genres: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get genres"
        )


@router.get("/artists")
async def get_popular_artists(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get popular artists."""
    try:
        service = RecommendationService(db)
        artists = await service.get_popular_artists(limit=limit)
        return {"artists": artists}
    except Exception as e:
        logger.error(f"Error getting artists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get artists"
        )


@router.get("/search", response_model=List[SongSearchResult])
async def search_songs(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search for songs or artists in the catalog."""
    try:
        service = RecommendationService(db)
        return await service.search_songs(query=query, limit=limit)
    except Exception as e:
        logger.error(f"Error searching songs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search songs"
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system database statistics."""
    try:
        service = RecommendationService(db)
        return await service.get_system_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system stats"
        )

