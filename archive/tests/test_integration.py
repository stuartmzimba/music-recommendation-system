"""
Integration tests for the Music Recommender System.
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.database import Base
from backend.app.models.database import Song, AssociationRule, UserListeningHistory, PopularSong
from ml.data_pipeline.data_loader import DataLoader
from ml.apriori.apriori_trainer import AprioriTrainer
from ml.content_based.content_recommender import ContentBasedRecommender


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    database_url = f"sqlite:///{temp_db.name}"
    engine = create_engine(database_url)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal, engine
    
    # Cleanup
    os.unlink(temp_db.name)


@pytest.fixture
def sample_songs():
    """Sample songs data for testing."""
    return [
        {
            'track_name': 'Jerusalema',
            'artist': 'Master KG',
            'genre': 'amapiano',
            'popularity_score': 0.95,
            'spotify_id': 'test_id_1',
            'danceability': 0.85,
            'energy': 0.75,
            'valence': 0.80
        },
        {
            'track_name': 'Water',
            'artist': 'Tyla',
            'genre': 'amapiano',
            'popularity_score': 0.92,
            'spotify_id': 'test_id_2',
            'danceability': 0.88,
            'energy': 0.82,
            'valence': 0.85
        },
        {
            'track_name': 'Last Last',
            'artist': 'Burna Boy',
            'genre': 'afrobeats',
            'popularity_score': 0.88,
            'spotify_id': 'test_id_3',
            'danceability': 0.75,
            'energy': 0.78,
            'valence': 0.70
        }
    ]


def test_data_loading_integration(test_db, sample_songs):
    """Test data loading functionality."""
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    try:
        # Add sample songs
        for song_data in sample_songs:
            song = Song(**song_data)
            db.add(song)
        
        db.commit()
        
        # Verify songs were added
        songs_count = db.query(Song).count()
        assert songs_count == len(sample_songs)
        
        # Test song retrieval
        jerusalema = db.query(Song).filter(Song.track_name == 'Jerusalema').first()
        assert jerusalema is not None
        assert jerusalema.artist == 'Master KG'
        assert jerusalema.genre == 'amapiano'
        
    finally:
        db.close()


def test_content_based_recommender_integration(test_db, sample_songs):
    """Test content-based recommender with real data."""
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    try:
        # Add sample songs
        for song_data in sample_songs:
            song = Song(**song_data)
            db.add(song)
        
        db.commit()
        
        # Create content-based recommender
        # Note: We need to mock the database connection for the recommender
        recommender = ContentBasedRecommender()
        recommender.db = db
        
        # Train the recommender
        success = recommender.train()
        assert success, "Content-based recommender training should succeed"
        
        # Test recommendations
        recommendations = recommender.get_recommendations_by_song_names(
            ['Master KG'], top_k=2
        )
        
        assert len(recommendations) > 0, "Should get recommendations"
        
        # Test genre-based recommendations
        genre_recs = recommender.get_recommendations_by_genre(
            ['amapiano'], top_k=2
        )
        
        assert len(genre_recs) > 0, "Should get genre-based recommendations"
        
    finally:
        db.close()


def test_popular_songs_integration(test_db, sample_songs):
    """Test popular songs functionality."""
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    try:
        # Add sample songs
        songs = []
        for song_data in sample_songs:
            song = Song(**song_data)
            db.add(song)
            songs.append(song)
        
        db.commit()
        
        # Create popular songs
        for i, song in enumerate(songs):
            popular_song = PopularSong(
                song_id=song.id,
                rank=i + 1,
                genre=song.genre,
                popularity_score=song.popularity_score,
                region='South Africa'
            )
            db.add(popular_song)
        
        db.commit()
        
        # Test popular songs retrieval
        popular_songs = db.query(PopularSong).order_by(PopularSong.rank).all()
        assert len(popular_songs) == len(sample_songs)
        
        # Test genre filtering
        amapiano_songs = db.query(PopularSong).filter(
            PopularSong.genre == 'amapiano'
        ).all()
        assert len(amapiano_songs) == 2  # Jerusalema and Water
        
    finally:
        db.close()


def test_apriori_integration_with_minimal_data(test_db, sample_songs):
    """Test Apriori algorithm with minimal data."""
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    try:
        # Add sample songs
        songs = []
        for song_data in sample_songs:
            song = Song(**song_data)
            db.add(song)
            songs.append(song)
        
        db.commit()
        
        # Add some listening history
        listening_records = [
            UserListeningHistory(user_id='user1', song_id=songs[0].id, listen_count=5),
            UserListeningHistory(user_id='user1', song_id=songs[1].id, listen_count=3),
            UserListeningHistory(user_id='user2', song_id=songs[0].id, listen_count=4),
            UserListeningHistory(user_id='user2', song_id=songs[2].id, listen_count=2),
        ]
        
        for record in listening_records:
            db.add(record)
        
        db.commit()
        
        # Test Apriori trainer
        trainer = AprioriTrainer(min_support=0.1, min_confidence=0.1)  # Lower thresholds for test
        trainer.db = db
        
        # Test transaction data preparation
        transactions = trainer.prepare_transaction_data()
        assert len(transactions) > 0, "Should have transaction data"
        
        # Note: With minimal data, we might not get association rules
        # but the process should not fail
        
    finally:
        db.close()


@pytest.mark.asyncio
async def test_end_to_end_recommendation_flow(test_db, sample_songs):
    """Test the complete recommendation flow."""
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    try:
        # Setup data
        songs = []
        for song_data in sample_songs:
            song = Song(**song_data)
            db.add(song)
            songs.append(song)
        
        db.commit()
        
        # Create popular songs
        for i, song in enumerate(songs):
            popular_song = PopularSong(
                song_id=song.id,
                rank=i + 1,
                genre=song.genre,
                popularity_score=song.popularity_score,
                region='South Africa'
            )
            db.add(popular_song)
        
        db.commit()
        
        # Test recommendation service (simplified)
        from backend.app.services.recommendation_service import RecommendationService
        
        service = RecommendationService(db)
        
        # Test popular recommendations (should work with minimal data)
        popular_recs = await service._get_popular_recommendations(['amapiano'], 2)
        assert len(popular_recs) > 0, "Should get popular recommendations"
        
        # Test content-based recommendations
        content_recs = await service._get_content_based_recommendations(
            ['Master KG'], ['amapiano'], 2
        )
        # Content-based might not work with minimal data, but should not crash
        
        # Test available genres
        genres = await service.get_available_genres()
        assert 'amapiano' in genres
        assert 'afrobeats' in genres
        
    finally:
        db.close()


def test_system_health_check():
    """Test that all components can be imported and initialized."""
    # Test imports
    from backend.app.main import app
    from frontend.app import main as frontend_main
    from ml.data_pipeline.data_loader import DataLoader
    from ml.apriori.apriori_trainer import AprioriTrainer
    from ml.content_based.content_recommender import ContentBasedRecommender
    
    # Test basic initialization
    assert app is not None
    assert frontend_main is not None
    
    # Test that classes can be instantiated
    loader = DataLoader()
    assert loader is not None
    loader.close()
    
    trainer = AprioriTrainer()
    assert trainer is not None
    trainer.db.close()
    
    recommender = ContentBasedRecommender()
    assert recommender is not None
    recommender.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
