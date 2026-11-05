"""
Recommendation service implementing hybrid recommendation logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from typing import List, Optional, Dict, Any
import logging
import json
import time
import sys
import os

# -------------------------------
# Ensure project root is in sys.path
# -------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# -------------------------------
# Imports
# -------------------------------
from backend.app.core.database import get_redis
from backend.app.core.config import settings
from backend.app.models.database import Song, AssociationRule, PopularSong, UserListeningHistory
from backend.app.models.schemas import (
    RecommendationResponse,
    RecommendationReason,
    PopularSongsResponse,
    SongSearchResult,
    SystemStatsResponse
)
from ml.content_based.content_recommender import get_content_recommender

logger = logging.getLogger(__name__)

# Simple in-memory LRU/TTL cache for environments without Redis
_IN_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}
_MAX_CACHE_ENTRIES = 500


class RecommendationService:
    """Service for generating music recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis()
        # Retrieve singleton ContentBasedRecommender instance
        self.content_recommender = get_content_recommender()

    async def get_recommendations(
        self,
        basket: List[str],
        genres: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[RecommendationResponse]:
        """Get hybrid recommendations using Apriori -> Content-based -> Popular fallback."""
        cache_key = self._get_cache_key(basket, genres, user_id, top_k)
        
        # 1. Check Redis cache
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    logger.info("Returning cached recommendations (Redis)")
                    return [RecommendationResponse(**item) for item in json.loads(cached)]
            except Exception as e:
                logger.warning(f"Redis cache lookup error: {e}")

        # 2. Check In-memory fallback cache
        if cache_key in _IN_MEMORY_CACHE:
            entry = _IN_MEMORY_CACHE[cache_key]
            if time.time() - entry["timestamp"] < getattr(settings, "CACHE_TTL", 3600):
                logger.info("Returning cached recommendations (In-Memory)")
                return [RecommendationResponse(**item) for item in entry["data"]]

        recommendations: List[RecommendationResponse] = []
        seen_spotify_ids = set()

        # Clean inputs
        clean_basket = [b.strip() for b in basket if b and b.strip()] if basket else []
        clean_genres = [g.strip() for g in genres if g and g.strip()] if genres else []

        # 0. Intelligent artist/song seed expansion & genre inference
        inferred_genres = set()
        if clean_basket:
            for item in clean_basket:
                # Find matches by artist or track title
                matched_songs = (
                    self.db.query(Song)
                    .filter(or_(Song.artist.ilike(f"%{item}%"), Song.track_name.ilike(f"%{item}%")))
                    .order_by(desc(Song.popularity_score))
                    .limit(4)
                    .all()
                )
                for s in matched_songs:
                    if s.genre:
                        inferred_genres.add(s.genre.strip())
                    # Include top popular tracks of seed artist/song for direct relevance
                    if s.spotify_id and s.spotify_id not in seen_spotify_ids and len(recommendations) < 3:
                        seen_spotify_ids.add(s.spotify_id)
                        recommendations.append(RecommendationResponse(
                            track_name=s.track_name,
                            artist=s.artist,
                            score=0.96,
                            reason=RecommendationReason.CONTENT_BASED,
                            genre=s.genre,
                            spotify_id=s.spotify_id
                        ))

            # If user didn't specify genres, augment with inferred genres so fallbacks stay contextually accurate
            if not clean_genres and inferred_genres:
                clean_genres = list(inferred_genres)

        # 1. Apriori-based recommendations
        if clean_basket:
            apriori_recs = await self._get_apriori_recommendations(clean_basket, clean_genres, top_k)
            for rec in apriori_recs:
                if rec.spotify_id:
                    seen_spotify_ids.add(rec.spotify_id)
                recommendations.append(rec)

        # 2. Content-based recommendations
        if len(recommendations) < top_k:
            remaining = top_k - len(recommendations)
            content_recs = await self._get_content_based_recommendations(
                clean_basket, clean_genres, remaining, exclude_ids=list(seen_spotify_ids)
            )
            for rec in content_recs:
                if len(recommendations) >= top_k:
                    break
                if rec.spotify_id and rec.spotify_id in seen_spotify_ids:
                    continue
                if rec.spotify_id:
                    seen_spotify_ids.add(rec.spotify_id)
                recommendations.append(rec)

        # 3. Popular songs fallback
        if len(recommendations) < top_k:
            remaining = top_k - len(recommendations)
            popular_recs = await self._get_popular_recommendations(
                clean_genres, remaining, exclude_ids=list(seen_spotify_ids)
            )
            for rec in popular_recs:
                if len(recommendations) >= top_k:
                    break
                if rec.spotify_id and rec.spotify_id in seen_spotify_ids:
                    continue
                if rec.spotify_id:
                    seen_spotify_ids.add(rec.spotify_id)
                recommendations.append(rec)

        final_recs = recommendations[:top_k]

        # Cache results in Redis
        if self.redis and final_recs:
            try:
                self.redis.setex(
                    cache_key,
                    getattr(settings, "CACHE_TTL", 3600),
                    json.dumps([r.model_dump() for r in final_recs])
                )
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")

        # Cache results in memory
        if final_recs:
            if len(_IN_MEMORY_CACHE) > _MAX_CACHE_ENTRIES:
                _IN_MEMORY_CACHE.clear()
            _IN_MEMORY_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": [r.model_dump() for r in final_recs]
            }

        return final_recs

    async def _get_apriori_recommendations(
        self, 
        basket: List[str], 
        genres: List[str], 
        top_k: int
    ) -> List[RecommendationResponse]:
        recommendations = []
        if not basket:
            return recommendations

        try:
            conditions = []
            for item in basket:
                pattern = f"%{item}%"
                conditions.append(Song.track_name.ilike(pattern))
                conditions.append(Song.artist.ilike(pattern))

            if not conditions:
                return recommendations

            basket_songs = self.db.query(Song).filter(or_(*conditions)).limit(50).all()

            if not basket_songs:
                logger.info("No matching songs found for basket items")
                return recommendations

            basket_song_ids = [song.id for song in basket_songs]
            genres_lower = [g.lower() for g in genres] if genres else []

            # Query rules matching basket items
            query = self.db.query(AssociationRule).filter(
                AssociationRule.antecedent_song_id.in_(basket_song_ids)
            )

            # Join consequent song to allow genre filtering and metadata access
            query = query.join(Song, AssociationRule.consequent_song_id == Song.id)
            if genres_lower:
                query = query.filter(func.lower(Song.genre).in_(genres_lower))

            rules = query.order_by(desc(AssociationRule.confidence), desc(AssociationRule.lift)).limit(top_k * 3).all()

            seen_songs = set(basket_song_ids)
            for rule in rules:
                if len(recommendations) >= top_k:
                    break
                consequent_song = rule.consequent_song
                if consequent_song.id not in seen_songs:
                    # Score combines confidence and lift
                    combined_score = round(float(rule.confidence), 3)
                    recommendations.append(RecommendationResponse(
                        track_name=consequent_song.track_name,
                        artist=consequent_song.artist,
                        score=combined_score,
                        reason=RecommendationReason.APRIORI,
                        genre=consequent_song.genre,
                        spotify_id=consequent_song.spotify_id
                    ))
                    seen_songs.add(consequent_song.id)

            logger.info(f"Generated {len(recommendations)} Apriori recommendations")
        except Exception as e:
            logger.error(f"Error in Apriori recommendations: {e}")

        return recommendations

    async def _get_content_based_recommendations(
        self,
        basket: List[str],
        genres: Optional[List[str]],
        top_k: int,
        exclude_ids: Optional[List[str]] = None
    ) -> List[RecommendationResponse]:
        recommendations = []
        exclude_ids = set(exclude_ids or [])

        try:
            content_recs = []
            if basket and hasattr(self.content_recommender, "get_recommendations_by_song_names"):
                content_recs = self.content_recommender.get_recommendations_by_song_names(
                    basket, top_k * 2, exclude_song_names=[]
                )
            
            # If basket didn't produce enough and genres provided, fill with genre recommendations
            if len(content_recs) < top_k and genres and hasattr(self.content_recommender, "get_recommendations_by_genre"):
                genre_recs = self.content_recommender.get_recommendations_by_genre(
                    genres, top_k * 2, exclude_song_names=basket
                )
                content_recs.extend(genre_recs)

            seen_titles = set()
            for rec in content_recs:
                if len(recommendations) >= top_k:
                    break
                spotify_id = rec.get("spotify_id")
                title_key = (rec.get("track_name", "").lower(), rec.get("artist", "").lower())
                if (spotify_id and spotify_id in exclude_ids) or title_key in seen_titles:
                    continue

                seen_titles.add(title_key)
                if spotify_id:
                    exclude_ids.add(spotify_id)

                recommendations.append(RecommendationResponse(
                    track_name=rec["track_name"],
                    artist=rec["artist"],
                    score=round(float(rec.get("score", 0.8)), 3),
                    reason=RecommendationReason.CONTENT_BASED,
                    genre=rec.get("genre"),
                    spotify_id=spotify_id
                ))

            logger.info(f"Generated {len(recommendations)} content-based recommendations")
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {e}")

        return recommendations

    async def _get_popular_recommendations(
        self,
        genres: Optional[List[str]],
        top_k: int,
        exclude_ids: Optional[List[str]] = None
    ) -> List[RecommendationResponse]:
        recommendations = []
        exclude_ids = set(exclude_ids or [])
        genres_lower = [g.lower() for g in genres] if genres else []

        try:
            # Query PopularSong table first
            query = self.db.query(PopularSong).join(Song, PopularSong.song_id == Song.id)
            if genres_lower:
                query = query.filter(func.lower(PopularSong.genre).in_(genres_lower))
            if exclude_ids:
                query = query.filter(~Song.spotify_id.in_(exclude_ids))

            popular_songs = query.order_by(PopularSong.rank).limit(top_k).all()

            for pop_song in popular_songs:
                song = pop_song.song
                if song.spotify_id and song.spotify_id in exclude_ids:
                    continue
                recommendations.append(RecommendationResponse(
                    track_name=song.track_name,
                    artist=song.artist,
                    score=round(float(pop_song.popularity_score), 2),
                    reason=RecommendationReason.POPULAR,
                    genre=song.genre,
                    spotify_id=song.spotify_id
                ))
                if song.spotify_id:
                    exclude_ids.add(song.spotify_id)

            # If still needed, query Song table directly by popularity_score
            if len(recommendations) < top_k:
                remaining = top_k - len(recommendations)
                song_query = self.db.query(Song)
                if genres_lower:
                    song_query = song_query.filter(func.lower(Song.genre).in_(genres_lower))
                if exclude_ids:
                    song_query = song_query.filter(~Song.spotify_id.in_(exclude_ids))

                additional_songs = song_query.order_by(desc(Song.popularity_score)).limit(remaining).all()
                for song in additional_songs:
                    recommendations.append(RecommendationResponse(
                        track_name=song.track_name,
                        artist=song.artist,
                        score=round(float(song.popularity_score or 50.0), 2),
                        reason=RecommendationReason.POPULAR,
                        genre=song.genre,
                        spotify_id=song.spotify_id
                    ))

            logger.info(f"Generated {len(recommendations)} popular recommendations")
        except Exception as e:
            logger.error(f"Error in popular recommendations: {e}")

        return recommendations

    async def get_popular_songs(
        self,
        limit: int = 20,
        genre: Optional[str] = None
    ) -> List[PopularSongsResponse]:
        """Get popular songs, optionally filtered by genre."""
        try:
            query = self.db.query(PopularSong).join(Song, PopularSong.song_id == Song.id)
            if genre and genre.strip().lower() != "all":
                query = query.filter(func.lower(PopularSong.genre) == genre.strip().lower())

            popular_records = query.order_by(PopularSong.rank).limit(limit).all()

            results = []
            for record in popular_records:
                results.append(PopularSongsResponse(
                    track_name=record.song.track_name,
                    artist=record.song.artist,
                    popularity_score=round(float(record.popularity_score), 2),
                    genre=record.genre or record.song.genre,
                    spotify_id=record.song.spotify_id
                ))

            # Fallback to Song table if popular_songs has fewer entries than requested
            if len(results) < limit:
                remaining = limit - len(results)
                seen_ids = [r.spotify_id for r in results if r.spotify_id]
                song_query = self.db.query(Song)
                if genre and genre.strip().lower() != "all":
                    song_query = song_query.filter(func.lower(Song.genre) == genre.strip().lower())
                if seen_ids:
                    song_query = song_query.filter(~Song.spotify_id.in_(seen_ids))

                fallback_songs = song_query.order_by(desc(Song.popularity_score)).limit(remaining).all()
                for song in fallback_songs:
                    results.append(PopularSongsResponse(
                        track_name=song.track_name,
                        artist=song.artist,
                        popularity_score=round(float(song.popularity_score or 50.0), 2),
                        genre=song.genre,
                        spotify_id=song.spotify_id
                    ))

            return results
        except Exception as e:
            logger.error(f"Error retrieving popular songs: {e}")
            raise

    async def get_available_genres(self) -> List[str]:
        """Get list of distinct genres present in the database."""
        try:
            results = (
                self.db.query(Song.genre)
                .filter(Song.genre.isnot(None), Song.genre != "")
                .distinct()
                .all()
            )
            genres = sorted({r[0].strip() for r in results if r[0] and r[0].strip()})
            return genres
        except Exception as e:
            logger.error(f"Error retrieving available genres: {e}")
            raise

    async def get_popular_artists(self, limit: int = 50) -> List[str]:
        """Get list of popular artists ordered by popularity and song count."""
        try:
            results = (
                self.db.query(Song.artist)
                .filter(Song.artist.isnot(None), Song.artist != "")
                .group_by(Song.artist)
                .order_by(desc(func.avg(Song.popularity_score)), desc(func.count(Song.id)))
                .limit(limit)
                .all()
            )
            return [r[0].strip() for r in results if r[0] and r[0].strip()]
        except Exception as e:
            logger.error(f"Error retrieving popular artists: {e}")
            raise

    async def search_songs(self, query: str, limit: int = 20) -> List[SongSearchResult]:
        """Search songs with broad multi-token matching across title, artist, and genre."""
        try:
            tokens = [t.strip() for t in query.strip().split() if t.strip()]
            if not tokens:
                return []

            # 1. Match songs where ALL tokens appear across track_name, artist, or genre
            and_filters = [
                or_(
                    Song.track_name.ilike(f"%{t}%"),
                    Song.artist.ilike(f"%{t}%"),
                    Song.genre.ilike(f"%{t}%")
                )
                for t in tokens
            ]
            primary_songs = (
                self.db.query(Song)
                .filter(*and_filters)
                .order_by(desc(Song.popularity_score))
                .limit(limit)
                .all()
            )

            matched_ids = {s.id for s in primary_songs}
            songs = list(primary_songs)

            # 2. If fewer than limit and multiple tokens, expand with OR matching
            if len(songs) < limit and len(tokens) > 1:
                remaining = limit - len(songs)
                or_filters = [
                    or_(
                        Song.track_name.ilike(f"%{t}%"),
                        Song.artist.ilike(f"%{t}%"),
                        Song.genre.ilike(f"%{t}%")
                    )
                    for t in tokens
                ]
                secondary_query = self.db.query(Song).filter(or_(*or_filters))
                if matched_ids:
                    secondary_query = secondary_query.filter(~Song.id.in_(matched_ids))
                secondary_songs = (
                    secondary_query
                    .order_by(desc(Song.popularity_score))
                    .limit(remaining)
                    .all()
                )
                songs.extend(secondary_songs)

            return [
                SongSearchResult(
                    id=s.id,
                    track_name=s.track_name,
                    artist=s.artist,
                    genre=s.genre,
                    spotify_id=s.spotify_id,
                    popularity_score=s.popularity_score,
                    danceability=s.danceability,
                    energy=s.energy,
                    valence=s.valence,
                    tempo=s.tempo
                )
                for s in songs
            ]
        except Exception as e:
            logger.error(f"Error searching songs: {e}")
            return []

    async def get_system_stats(self) -> SystemStatsResponse:
        """Get database and system statistics."""
        try:
            songs_count = self.db.query(func.count(Song.id)).scalar() or 0
            genres_count = self.db.query(func.count(func.distinct(Song.genre))).filter(Song.genre.isnot(None), Song.genre != "").scalar() or 0
            rules_count = self.db.query(func.count(AssociationRule.id)).scalar() or 0
            history_count = self.db.query(func.count(UserListeningHistory.id)).scalar() or 0
            artists_count = self.db.query(func.count(func.distinct(Song.artist))).filter(Song.artist.isnot(None), Song.artist != "").scalar() or 0
            return SystemStatsResponse(
                songs_count=songs_count,
                genres_count=genres_count,
                rules_count=rules_count,
                history_count=history_count,
                artists_count=artists_count
            )
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise

    def _get_cache_key(
        self,
        basket: List[str],
        genres: Optional[List[str]],
        user_id: Optional[str],
        top_k: int
    ) -> str:
        """Generate cache key for recommendations."""
        key_parts = [
            "recommendations",
            "|".join(sorted([b.lower() for b in basket])) if basket else "empty_basket",
            "|".join(sorted([g.lower() for g in genres])) if genres else "no_genres",
            user_id or "no_user",
            str(top_k)
        ]
        return ":".join(key_parts)
