#!/usr/bin/env python3
"""
Load Only Spotify Data
Loads only Spotify-fetched songs into the database, skipping sample data.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ml"))

from ml.data_pipeline.data_loader import DataLoader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_spotify_data_only():
    """Load only Spotify data into the database."""
    
    logger.info("🎵 Loading ONLY Spotify data...")
    
    # Initialize data loader
    loader = DataLoader()
    
    # Specify only Spotify CSV files
    spotify_files = [
        "data/sample/spotify_simple_songs.csv"
    ]
    
    # Check if files exist
    existing_files = []
    for file_path in spotify_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            logger.info(f"✅ Found: {file_path}")
        else:
            logger.warning(f"❌ Missing: {file_path}")
    
    if not existing_files:
        logger.error("❌ No Spotify CSV files found!")
        return
    
    try:
        # Load songs from Spotify CSV files only
        total_loaded = 0
        for file_path in existing_files:
            logger.info(f"📁 Loading from: {file_path}")
            loaded = loader.load_songs_from_csv(file_path)
            total_loaded += loaded
            logger.info(f"   Loaded {loaded} songs")
        
        logger.info(f"✅ Total songs loaded: {total_loaded}")
        
        # Generate popular songs rankings based on Spotify popularity scores
        logger.info("📊 Generating popular songs rankings...")
        loader.generate_popular_songs()
        
        # Get final counts
        stats = loader.get_database_stats()
        
        logger.info("📈 Final database statistics:")
        logger.info(f"   Songs: {stats['total_songs']}")
        logger.info(f"   Popular songs: {stats['total_popular_songs']}")
        logger.info(f"   Unique genres: {stats['unique_genres']}")
        logger.info(f"   Unique artists: {stats['unique_artists']}")
        
        logger.info("🎉 Spotify data loading completed!")
        
    except Exception as e:
        logger.error(f"❌ Error loading Spotify data: {e}")
        raise

def main():
    """Main function."""
    print("🎵 SPOTIFY-ONLY DATA LOADER")
    print("=" * 50)
    print("This will load ONLY Spotify data (no sample data).")
    print("=" * 50)
    
    load_spotify_data_only()
    
    print("\n💡 Next steps:")
    print("   1. Restart your API server if it's running")
    print("   2. Refresh your frontend")
    print("   3. Enjoy pure Spotify music data!")

if __name__ == "__main__":
    main()
