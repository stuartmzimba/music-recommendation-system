#!/usr/bin/env python3
"""
Load Massive Dataset into Database
Loads 50,000+ songs and massive listening history into the database.
"""

import sqlite3
import pandas as pd
import os
from typing import List, Dict

class MassiveDatasetLoader:
    def __init__(self):
        """Initialize the massive dataset loader."""
        self.db_path = 'music_recommender.db'
        self.data_dir = 'data/sample'

    def clear_database(self):
        """Clear all existing data from the database."""
        print("🗑️ Clearing existing database data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear all tables
        tables = ['association_rules', 'user_listening_history', 'popular_songs', 'songs']
        
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')
            print(f"  ✅ Cleared {table}")
        
        conn.commit()
        conn.close()
        print("🗑️ Database cleared successfully!")

    def load_massive_songs(self, filename: str = "spotify_massive_songs.csv"):
        """Load massive song dataset into database."""
        filepath = os.path.join(self.data_dir, filename)

        # Try to find the latest intermediate file if main file doesn't exist
        if not os.path.exists(filepath):
            # Look for intermediate files
            import glob
            intermediate_files = glob.glob(os.path.join(self.data_dir, "spotify_massive_intermediate_*.csv"))
            if intermediate_files:
                # Get the latest intermediate file (highest number)
                latest_file = max(intermediate_files, key=lambda x: int(x.split('_')[-1].split('.')[0]))
                filepath = latest_file
                print(f"📁 Using latest intermediate file: {os.path.basename(filepath)}")
            else:
                print(f"❌ File not found: {filepath}")
                return False
        
        print(f"📊 Loading massive songs from {filepath}...")
        
        try:
            # Read CSV
            df = pd.read_csv(filepath)
            print(f"📈 Found {len(df):,} songs in CSV")
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert songs
            inserted_count = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO songs (
                            track_name, artist, genre, popularity_score, spotify_id,
                            danceability, energy, valence, tempo, acousticness,
                            instrumentalness, liveness, speechiness
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['track_name'], row['artist'], row['genre'], 
                        row['popularity_score'], row['spotify_id'],
                        row['danceability'], row['energy'], row['valence'], 
                        row['tempo'], row['acousticness'], row['instrumentalness'],
                        row['liveness'], row['speechiness']
                    ))
                    inserted_count += 1
                    
                    if inserted_count % 1000 == 0:
                        print(f"  📊 Inserted {inserted_count:,} songs...")
                        
                except Exception as e:
                    print(f"  ⚠️ Error inserting song: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully loaded {inserted_count:,} songs!")
            
            # Show genre distribution
            self.show_genre_distribution()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading songs: {e}")
            return False

    def load_massive_listening_history(self, filename: str = "massive_user_listening_history.csv"):
        """Load massive listening history into database."""
        filepath = os.path.join(self.data_dir, filename)

        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False

        print(f"🎧 Loading massive listening history from {filepath}...")

        try:
            # Read CSV
            df = pd.read_csv(filepath)
            print(f"📈 Found {len(df):,} listening records in CSV")

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create a mapping from track_name + artist to song_id
            print("🔍 Creating song mapping...")
            cursor.execute('SELECT id, track_name, artist FROM songs')
            songs = cursor.fetchall()
            song_map = {}
            for song_id, track_name, artist in songs:
                key = f"{track_name}_{artist}".lower()
                song_map[key] = song_id

            print(f"📊 Created mapping for {len(song_map):,} songs")

            # Insert listening history
            inserted_count = 0
            skipped_count = 0

            for _, row in df.iterrows():
                try:
                    # Find the song_id for this track
                    key = f"{row['track_name']}_{row['artist']}".lower()
                    song_id = song_map.get(key)

                    if song_id:
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_listening_history (
                                user_id, song_id, listen_count, last_listened
                            ) VALUES (?, ?, ?, ?)
                        ''', (
                            row['user_id'], song_id, row['listen_count'], row['last_listened']
                        ))
                        inserted_count += 1

                        if inserted_count % 5000 == 0:
                            print(f"  📊 Inserted {inserted_count:,} listening records...")
                    else:
                        skipped_count += 1

                except Exception as e:
                    print(f"  ⚠️ Error inserting listening record: {e}")
                    skipped_count += 1
                    continue

            conn.commit()
            conn.close()

            print(f"✅ Successfully loaded {inserted_count:,} listening records!")
            if skipped_count > 0:
                print(f"⚠️ Skipped {skipped_count:,} records (songs not found in database)")

            return True

        except Exception as e:
            print(f"❌ Error loading listening history: {e}")
            return False

    def generate_popular_songs(self):
        """Generate popular songs rankings from the loaded songs."""
        print("🏆 Generating popular songs rankings...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear existing popular songs
            cursor.execute('DELETE FROM popular_songs')

            # Get songs ordered by popularity
            cursor.execute('''
                SELECT id, genre, popularity_score
                FROM songs
                ORDER BY popularity_score DESC, track_name ASC
            ''')

            songs = cursor.fetchall()

            # Insert into popular_songs with rankings (using correct schema)
            for rank, song in enumerate(songs, 1):
                cursor.execute('''
                    INSERT INTO popular_songs (
                        song_id, rank, genre, popularity_score
                    ) VALUES (?, ?, ?, ?)
                ''', (song[0], rank, song[1], song[2]))

            conn.commit()
            conn.close()

            print(f"✅ Generated {len(songs):,} popular song rankings!")

            return True

        except Exception as e:
            print(f"❌ Error generating popular songs: {e}")
            return False

    def show_genre_distribution(self):
        """Show the distribution of genres in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT genre, COUNT(*) as count 
                FROM songs 
                GROUP BY genre 
                ORDER BY count DESC
            ''')
            
            genres = cursor.fetchall()
            conn.close()
            
            print(f"\n📊 Genre Distribution ({len(genres)} genres):")
            for genre, count in genres:
                print(f"  {genre}: {count:,} songs")
            
        except Exception as e:
            print(f"❌ Error showing genre distribution: {e}")

    def show_database_stats(self):
        """Show comprehensive database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Songs count
            cursor.execute('SELECT COUNT(*) FROM songs')
            songs_count = cursor.fetchone()[0]
            
            # Listening history count
            cursor.execute('SELECT COUNT(*) FROM user_listening_history')
            history_count = cursor.fetchone()[0]
            
            # Unique users
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_listening_history')
            users_count = cursor.fetchone()[0]
            
            # Popular songs count
            cursor.execute('SELECT COUNT(*) FROM popular_songs')
            popular_count = cursor.fetchone()[0]
            
            # Association rules count
            cursor.execute('SELECT COUNT(*) FROM association_rules')
            rules_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n📊 Database Statistics:")
            print(f"  🎵 Songs: {songs_count:,}")
            print(f"  🎧 Listening Records: {history_count:,}")
            print(f"  👥 Unique Users: {users_count:,}")
            print(f"  🏆 Popular Songs: {popular_count:,}")
            print(f"  🔗 Association Rules: {rules_count:,}")
            
        except Exception as e:
            print(f"❌ Error showing database stats: {e}")

def main():
    """Main function to load massive dataset."""
    try:
        loader = MassiveDatasetLoader()
        
        print("🚀 Starting massive dataset loading...")
        
        # Clear existing data
        loader.clear_database()
        
        # Load massive songs
        if not loader.load_massive_songs():
            print("❌ Failed to load songs")
            return False
        
        # Generate popular songs rankings
        if not loader.generate_popular_songs():
            print("❌ Failed to generate popular songs")
            return False
        
        # Check if listening history file exists and load it
        history_file = "massive_user_listening_history.csv"
        if os.path.exists(os.path.join(loader.data_dir, history_file)):
            if not loader.load_massive_listening_history():
                print("❌ Failed to load listening history")
                return False
        else:
            print(f"ℹ️ Listening history file not found: {history_file}")
            print("   You can generate it using generate_massive_listening_history.py")
        
        # Show final statistics
        loader.show_database_stats()
        
        print(f"\n🎉 SUCCESS! Massive dataset loaded successfully!")
        print(f"🎯 Ready for 50,000+ song recommendations with multiple genres!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
