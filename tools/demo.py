#!/usr/bin/env python3
"""
Demo script for the Music Recommender System.
This script demonstrates the key features of the system.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ml.data_pipeline.data_loader import DataLoader
from ml.apriori.apriori_trainer import AprioriTrainer
from ml.content_based.content_recommender import ContentBasedRecommender
from backend.app.services.recommendation_service import RecommendationService
from backend.app.core.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_recommendations(recommendations, title="Recommendations"):
    """Print recommendations in a formatted way."""
    print(f"\n🎵 {title}:")
    if not recommendations:
        print("   No recommendations found.")
        return
    
    for i, rec in enumerate(recommendations, 1):
        if hasattr(rec, 'track_name'):
            # RecommendationResponse object
            print(f"   {i}. {rec.track_name} - {rec.artist}")
            print(f"      Genre: {rec.genre or 'Unknown'} | Score: {rec.score:.3f} | Method: {rec.reason}")
        else:
            # Dictionary
            print(f"   {i}. {rec['track_name']} - {rec['artist']}")
            print(f"      Genre: {rec.get('genre', 'Unknown')} | Score: {rec['score']:.3f} | Method: {rec['reason']}")


async def demo_data_loading():
    """Demonstrate data loading functionality."""
    print_header("DATA LOADING DEMO")
    
    loader = DataLoader()
    
    try:
        # Load sample data
        print("📊 Loading sample data...")
        results = loader.load_sample_data()
        
        print(f"✅ Data loading results:")
        for key, value in results.items():
            print(f"   - {key}: {value}")
        
        # Show statistics
        stats = loader.get_data_statistics()
        print(f"\n📈 Database statistics:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    finally:
        loader.close()


async def demo_content_based_recommendations():
    """Demonstrate content-based recommendations."""
    print_header("CONTENT-BASED RECOMMENDATIONS DEMO")
    
    recommender = ContentBasedRecommender()
    
    try:
        # Train the recommender
        print("🤖 Training content-based recommender...")
        if not recommender.train():
            print("❌ Training failed")
            return False
        
        print("✅ Training completed!")
        
        # Test song-based recommendations
        print("\n🎯 Testing song-based recommendations...")
        test_songs = ["Master KG", "Amapiano"]
        recommendations = recommender.get_recommendations_by_song_names(test_songs, top_k=5)
        print_recommendations(recommendations, f"Similar to {test_songs}")
        
        # Test genre-based recommendations
        print("\n🎼 Testing genre-based recommendations...")
        test_genres = ["amapiano"]
        genre_recs = recommender.get_recommendations_by_genre(test_genres, top_k=5)
        print_recommendations(genre_recs, f"Top {test_genres} songs")
        
        return True
        
    except Exception as e:
        print(f"❌ Content-based recommendations failed: {e}")
        return False
    
    finally:
        recommender.close()


async def demo_apriori_training():
    """Demonstrate Apriori algorithm training."""
    print_header("APRIORI ALGORITHM DEMO")
    
    trainer = AprioriTrainer(min_support=0.05, min_confidence=0.3, limit_users=100)
    
    try:
        print("🤖 Training Apriori association rules...")
        results = trainer.train()
        
        if results['success']:
            print("✅ Apriori training completed!")
            print(f"📊 Training results:")
            for key, value in results.items():
                if key != 'success':
                    print(f"   - {key}: {value}")
        else:
            print(f"❌ Apriori training failed: {results.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Apriori training failed: {e}")
        return False


async def demo_hybrid_recommendations():
    """Demonstrate the hybrid recommendation system."""
    print_header("HYBRID RECOMMENDATION SYSTEM DEMO")
    
    db = SessionLocal()
    
    try:
        service = RecommendationService(db)
        
        # Test case 1: User likes Amapiano
        print("🎵 Test Case 1: User likes Amapiano music")
        basket = ["Master KG", "Amapiano"]
        genres = ["amapiano"]
        
        recommendations = await service.get_recommendations(
            basket=basket,
            genres=genres,
            top_k=5
        )
        
        print_recommendations(recommendations, "Hybrid Recommendations for Amapiano Fan")
        
        # Test case 2: User likes Afrobeats
        print("\n🎵 Test Case 2: User likes Afrobeats")
        basket = ["Burna Boy", "Wizkid"]
        genres = ["afrobeats"]
        
        recommendations = await service.get_recommendations(
            basket=basket,
            genres=genres,
            top_k=5
        )
        
        print_recommendations(recommendations, "Hybrid Recommendations for Afrobeats Fan")
        
        # Test case 3: Mixed preferences
        print("\n🎵 Test Case 3: Mixed music preferences")
        basket = ["Master KG", "Burna Boy", "Tyla"]
        
        recommendations = await service.get_recommendations(
            basket=basket,
            top_k=5
        )
        
        print_recommendations(recommendations, "Hybrid Recommendations for Mixed Preferences")
        
        # Show popular songs
        print("\n🔥 Popular songs in South Africa:")
        popular_songs = await service.get_popular_songs(limit=5)
        
        for i, song in enumerate(popular_songs, 1):
            print(f"   {i}. {song.track_name} - {song.artist}")
            print(f"      Genre: {song.genre or 'Unknown'} | Score: {song.popularity_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid recommendations failed: {e}")
        return False
    
    finally:
        db.close()


async def demo_api_endpoints():
    """Demonstrate API functionality."""
    print_header("API ENDPOINTS DEMO")
    
    db = SessionLocal()
    
    try:
        service = RecommendationService(db)
        
        # Test genres endpoint
        print("🎼 Available genres:")
        genres = await service.get_available_genres()
        print(f"   {', '.join(genres)}")
        
        # Test artists endpoint
        print("\n🎤 Popular artists:")
        artists = await service.get_popular_artists(limit=10)
        for i, artist in enumerate(artists[:5], 1):
            print(f"   {i}. {artist}")
        
        return True
        
    except Exception as e:
        print(f"❌ API demo failed: {e}")
        return False
    
    finally:
        db.close()


async def main():
    """Main demo function."""
    print("🎵 MUSIC RECOMMENDER SYSTEM DEMO")
    print("=" * 60)
    print("This demo showcases the hybrid music recommendation system")
    print("with Apriori, content-based, and popularity-based methods.")
    
    success_count = 0
    total_demos = 5
    
    # Run all demos
    demos = [
        demo_data_loading,
        demo_content_based_recommendations,
        demo_apriori_training,
        demo_hybrid_recommendations,
        demo_api_endpoints
    ]
    
    for demo in demos:
        try:
            if await demo():
                success_count += 1
        except Exception as e:
            logger.error(f"Demo failed: {e}")
    
    # Summary
    print_header("DEMO SUMMARY")
    print(f"✅ Completed: {success_count}/{total_demos} demos")
    
    if success_count == total_demos:
        print("🎉 All demos completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Start the API: uvicorn backend.app.main:app --reload")
        print("   2. Start the frontend: streamlit run frontend/app.py")
        print("   3. Or use Docker: docker-compose up --build")
    else:
        print("⚠️  Some demos failed. Check the logs above for details.")
    
    print("\n📖 See README.md for more information.")


if __name__ == "__main__":
    asyncio.run(main())
