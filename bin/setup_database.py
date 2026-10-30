#!/usr/bin/env python3
"""
Database setup script for Music Recommender System
Supports both PostgreSQL and SQLite backends
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.models.database import (
    Song, AssociationRule, UserListeningHistory, PopularSong
)
from ml.data_pipeline.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def show_database_info():
    """Show database configuration info"""
    logger.info("=== DATABASE CONFIGURATION ===")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    if settings.DATABASE_URL.startswith("postgresql"):
        logger.info("Database Type: PostgreSQL")
        logger.info("Requirements:")
        logger.info("  - PostgreSQL server must be running")
        logger.info("  - Database 'music_recommender' must exist")
        logger.info("  - User must have proper permissions")
    elif settings.DATABASE_URL.startswith("sqlite"):
        logger.info("Database Type: SQLite")
        logger.info("Requirements:")
        logger.info("  - No server required")
        logger.info("  - Database file will be created automatically")

def load_sample_data():
    """Load sample data from CSV files"""
    try:
        logger.info("Loading sample data from CSV files...")
        data_loader = DataLoader()
        results = data_loader.load_sample_data()
        data_loader.close()

        logger.info("✅ Sample data loaded successfully!")
        logger.info(f"   - Songs: {results['songs']}")
        logger.info(f"   - Listening history: {results['listening_history']}")
        logger.info(f"   - Popular songs: {results['popular_songs']}")
        return True
    except Exception as e:
        logger.error(f"❌ Error loading sample data: {e}")
        return False

def main():
    """Main setup function"""
    print("🎵 MUSIC RECOMMENDER DATABASE SETUP")
    print("=" * 50)

    # Show configuration
    show_database_info()
    print()

    # Test connection
    if not test_database_connection():
        print("\n❌ Setup failed: Cannot connect to database")
        print("\nFor PostgreSQL:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Create database: createdb music_recommender")
        print("3. Update connection settings in .env file")
        print("\nFor SQLite:")
        print("1. Change DATABASE_URL in backend/app/core/config.py to:")
        print('   DATABASE_URL: str = "sqlite:///./music_recommender.db"')
        return False

    # Create tables
    if not create_database_tables():
        print("\n❌ Setup failed: Cannot create tables")
        return False

    # Load sample data
    if not load_sample_data():
        print("\n⚠️  Warning: Failed to load sample data")
        print("You can manually load data later using:")
        print("python -c \"from ml.data_pipeline.data_loader import DataLoader; DataLoader().load_sample_data()\"")

    print("\n✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python demo.py")
    print("2. Or start the API: uvicorn backend.app.main:app --reload")
    print("3. Or start Streamlit: streamlit run frontend/streamlit_app.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
