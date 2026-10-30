#!/usr/bin/env python3
"""
Database setup script for the Music Recommender System.
This script creates the database tables and loads initial data.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.database import engine, Base
from backend.app.models.database import Song, AssociationRule, UserListeningHistory, PopularSong

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("🚀 Setting up Music Recommender database...")
    
    # Create tables
    if not create_tables():
        logger.error("❌ Database setup failed!")
        return False
    
    logger.info("🎉 Database setup completed successfully!")
    logger.info("💡 Next steps:")
    logger.info("   1. Run 'python scripts/train_models.py' to load data and train models")
    logger.info("   2. Start the API with 'docker-compose up' or 'uvicorn backend.app.main:app --reload'")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
