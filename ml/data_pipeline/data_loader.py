"""
Data loading and ETL pipeline for the Music Recommender System.
"""

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional

from backend.app.core.database import SessionLocal
from backend.app.models.database import Song, UserListeningHistory, PopularSong

logger = logging.getLogger(__name__)


class DataLoader:
    """Data loader for ETL operations."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    
    def load_songs_from_csv(self, csv_path: str) -> int:
        """Load songs from CSV file into database."""
        logger.info(f"Loading songs from {csv_path}")
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_cols = ['track_name', 'artist', 'genre', 'popularity_score']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            loaded_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Check if song already exists
                    existing_song = self.db.query(Song).filter(
                        Song.track_name == row['track_name'],
                        Song.artist == row['artist']
                    ).first()
                    
                    if existing_song:
                        # Update existing song
                        existing_song.genre = row.get('genre')
                        existing_song.popularity_score = row.get('popularity_score', 0.0)
                        existing_song.spotify_id = row.get('spotify_id')
                        existing_song.danceability = row.get('danceability')
                        existing_song.energy = row.get('energy')
                        existing_song.valence = row.get('valence')
                        existing_song.tempo = row.get('tempo')
                        existing_song.acousticness = row.get('acousticness')
                        existing_song.instrumentalness = row.get('instrumentalness')
                        existing_song.liveness = row.get('liveness')
                        existing_song.speechiness = row.get('speechiness')
                    else:
                        # Create new song
                        song = Song(
                            track_name=row['track_name'],
                            artist=row['artist'],
                            genre=row.get('genre'),
                            spotify_id=row.get('spotify_id'),
                            popularity_score=row.get('popularity_score', 0.0),
                            danceability=row.get('danceability'),
                            energy=row.get('energy'),
                            valence=row.get('valence'),
                            tempo=row.get('tempo'),
                            acousticness=row.get('acousticness'),
                            instrumentalness=row.get('instrumentalness'),
                            liveness=row.get('liveness'),
                            speechiness=row.get('speechiness')
                        )
                        self.db.add(song)
                    
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Error loading song {row.get('track_name', 'Unknown')}: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"Successfully loaded {loaded_count} songs")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading songs from CSV: {e}")
            self.db.rollback()
            return 0

    def load_all_songs_from_csvs(self, force_reload: bool = False) -> int:
        """Load songs from all CSV files in the data/sample directory."""
        try:
            # Check if songs already exist
            existing_count = self.db.query(Song).count()
            if existing_count > 0 and not force_reload:
                logger.info(f"Database already contains {existing_count} songs. Use force_reload=True to reload.")
                return existing_count

            # Clear existing songs if force reload
            if force_reload and existing_count > 0:
                logger.info("Force reload: clearing existing songs...")
                self.db.query(Song).delete()
                self.db.commit()

            # Find all CSV files with songs
            sample_dir = os.path.join(self.data_dir, 'sample')
            csv_files = [
                "south_african_songs.csv",
                "international_songs.csv",
                "african_songs.csv",
                "spotify_fetched_songs.csv",
                "spotify_south_african_songs.csv",
                "spotify_international_songs.csv",
                "spotify_simple_songs.csv"
            ]

            total_songs_added = 0

            for csv_filename in csv_files:
                csv_path = os.path.join(sample_dir, csv_filename)
                if not os.path.exists(csv_path):
                    logger.warning(f"CSV file not found: {csv_path} (skipping)")
                    continue

                logger.info(f"Loading songs from {csv_filename}...")
                songs_added = self.load_songs_from_csv(csv_path)
                total_songs_added += songs_added
                logger.info(f"Added {songs_added} songs from {csv_filename}")

            logger.info(f"Successfully loaded {total_songs_added} total songs from all CSV files")
            return total_songs_added

        except Exception as e:
            logger.error(f"Error loading songs from multiple CSVs: {e}")
            self.db.rollback()
            return 0

    def load_listening_history_from_csv(self, csv_path: str) -> int:
        """Load user listening history from CSV file."""
        logger.info(f"Loading listening history from {csv_path}")
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_cols = ['user_id', 'track_name', 'artist']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            loaded_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Find the song
                    song = self.db.query(Song).filter(
                        Song.track_name == row['track_name'],
                        Song.artist == row['artist']
                    ).first()
                    
                    if not song:
                        logger.warning(f"Song not found: {row['track_name']} - {row['artist']}")
                        continue
                    
                    # Check if listening record already exists
                    existing_record = self.db.query(UserListeningHistory).filter(
                        UserListeningHistory.user_id == row['user_id'],
                        UserListeningHistory.song_id == song.id
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        existing_record.listen_count = row.get('listen_count', 1)
                        if 'last_listened' in row and pd.notna(row['last_listened']):
                            existing_record.last_listened = pd.to_datetime(row['last_listened'])
                    else:
                        # Create new record
                        listening_record = UserListeningHistory(
                            user_id=row['user_id'],
                            song_id=song.id,
                            listen_count=row.get('listen_count', 1),
                            last_listened=pd.to_datetime(row['last_listened']) if 'last_listened' in row and pd.notna(row['last_listened']) else datetime.now()
                        )
                        self.db.add(listening_record)
                    
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Error loading listening record for user {row.get('user_id', 'Unknown')}: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"Successfully loaded {loaded_count} listening records")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading listening history from CSV: {e}")
            self.db.rollback()
            return 0
    
    def generate_popular_songs(self) -> int:
        """Generate popular songs table based on song popularity scores."""
        logger.info("Generating popular songs table...")
        
        try:
            # Clear existing popular songs
            self.db.query(PopularSong).delete()
            
            # Get songs ordered by popularity
            songs = self.db.query(Song).filter(
                Song.popularity_score.isnot(None)
            ).order_by(Song.popularity_score.desc()).all()
            
            # Create popular songs records
            for rank, song in enumerate(songs, 1):
                popular_song = PopularSong(
                    song_id=song.id,
                    rank=rank,
                    genre=song.genre,
                    popularity_score=song.popularity_score,
                    region="South Africa"
                )
                self.db.add(popular_song)
            
            self.db.commit()
            logger.info(f"Generated {len(songs)} popular songs records")
            return len(songs)
            
        except Exception as e:
            logger.error(f"Error generating popular songs: {e}")
            self.db.rollback()
            return 0
    
    def load_sample_data(self) -> Dict[str, int]:
        """Load all sample data from the data/sample directory."""
        logger.info("Loading sample data...")
        
        # Get the project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        sample_data_dir = os.path.join(project_root, "data", "sample")
        
        results = {}
        
        # Load songs: prefer full catalog spotify_massive_songs.csv (includes Kendrick Lamar, Drake, Hip-Hop, Pop, etc.)
        # combined with south_african_songs.csv
        total_songs = 0
        massive_file = os.path.join(sample_data_dir, "spotify_massive_songs.csv")
        if os.path.exists(massive_file):
            total_songs += self.load_songs_from_csv(massive_file)

        sa_file = os.path.join(sample_data_dir, "south_african_songs.csv")
        if os.path.exists(sa_file):
            total_songs += self.load_songs_from_csv(sa_file)

        results['songs'] = total_songs
        
        # Load listening history
        history_file = os.path.join(sample_data_dir, "user_listening_history.csv")
        if os.path.exists(history_file):
            results['listening_history'] = self.load_listening_history_from_csv(history_file)
        else:
            logger.warning(f"Listening history file not found: {history_file}")
            results['listening_history'] = 0
        
        # Generate popular songs
        results['popular_songs'] = self.generate_popular_songs()
        
        logger.info(f"Sample data loading completed: {results}")
        return results
    
    def get_data_statistics(self) -> Dict[str, int]:
        """Get statistics about the loaded data."""
        try:
            stats = {
                'total_songs': self.db.query(Song).count(),
                'total_users': self.db.query(UserListeningHistory.user_id).distinct().count(),
                'total_listening_records': self.db.query(UserListeningHistory).count(),
                'total_popular_songs': self.db.query(PopularSong).count(),
                'unique_genres': self.db.query(Song.genre).distinct().count(),
                'unique_artists': self.db.query(Song.artist).distinct().count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            return {}
    
    def load_sample_data(self, force_reload: bool = False) -> Dict[str, int]:
        """Load all sample data from CSV files."""
        logger.info("Loading sample data from CSV files...")

        results = {
            'songs': 0,
            'listening_history': 0,
            'popular_songs': 0
        }

        # Check if data already exists
        if not force_reload:
            existing_songs = self.db.query(Song).count()
            if existing_songs > 0:
                logger.info(f"Database already contains {existing_songs} songs. Use force_reload=True to reload.")
                return self._get_current_counts()

        # Load songs from all CSV files
        results['songs'] = self.load_all_songs_from_csvs(force_reload=force_reload)

        # Load listening history
        history_file = os.path.join(self.data_dir, 'sample', 'user_listening_history.csv')
        if os.path.exists(history_file):
            results['listening_history'] = self.load_listening_history_from_csv(history_file)
        else:
            logger.warning(f"Listening history file not found: {history_file}")

        # Generate popular songs
        results['popular_songs'] = self.generate_popular_songs()

        logger.info(f"Sample data loading completed: {results}")
        return results

    def _get_current_counts(self) -> Dict[str, int]:
        """Get current counts of data in database."""
        return {
            'songs': self.db.query(Song).count(),
            'listening_history': self.db.query(UserListeningHistory).count(),
            'popular_songs': self.db.query(PopularSong).count()
        }

    def close(self):
        """Close database connection."""
        self.db.close()


def main():
    """Main function for running data loading."""
    logging.basicConfig(level=logging.INFO)
    
    loader = DataLoader()
    
    try:
        # Load sample data
        results = loader.load_sample_data()
        
        # Print results
        print("✅ Data loading completed!")
        print(f"📊 Results:")
        for key, value in results.items():
            print(f"   - {key}: {value}")
        
        # Print statistics
        stats = loader.get_data_statistics()
        print(f"\n📈 Database Statistics:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
    
    finally:
        loader.close()


if __name__ == "__main__":
    main()
