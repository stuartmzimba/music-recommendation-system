#!/usr/bin/env python3
"""
Generate Massive User Listening History
Creates realistic listening patterns for 50,000+ songs with diverse user preferences.
"""

import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import sqlite3

class MassiveListeningHistoryGenerator:
    def __init__(self):
        """Initialize the listening history generator."""
        self.users = []
        self.songs = []
        self.listening_history = []
        
        # User preference profiles
        self.user_profiles = {
            'afrobeats_lover': {
                'preferred_genres': ['Afrobeats', 'Afrohouse', 'Dancehall', 'Reggae'],
                'weight': 0.7
            },
            'amapiano_fan': {
                'preferred_genres': ['Amapiano', 'Afrohouse', 'Gqom', 'Kwaito'],
                'weight': 0.8
            },
            'pop_mainstream': {
                'preferred_genres': ['Pop', 'Hip-Hop', 'R&B', 'Dance'],
                'weight': 0.6
            },
            'electronic_enthusiast': {
                'preferred_genres': ['Electronic', 'House', 'Techno', 'Trance', 'Dubstep'],
                'weight': 0.75
            },
            'rock_alternative': {
                'preferred_genres': ['Rock', 'Alternative', 'Indie', 'Folk'],
                'weight': 0.65
            },
            'latin_music_fan': {
                'preferred_genres': ['Reggaeton', 'Latin Pop', 'Salsa'],
                'weight': 0.8
            },
            'jazz_soul_lover': {
                'preferred_genres': ['Jazz', 'Neo-Soul', 'Soul', 'Funk', 'Blues'],
                'weight': 0.7
            },
            'world_music_explorer': {
                'preferred_genres': ['Bollywood', 'K-Pop', 'J-Pop', 'Classical', 'Gospel'],
                'weight': 0.6
            },
            'diverse_listener': {
                'preferred_genres': [],  # Listens to everything
                'weight': 0.3
            }
        }

    def load_songs_from_database(self):
        """Load songs from the database."""
        try:
            conn = sqlite3.connect('music_recommender.db')
            query = "SELECT track_name, artist, genre, popularity_score FROM songs"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            self.songs = df.to_dict('records')
            print(f"📊 Loaded {len(self.songs):,} songs from database")
            
            # Show genre distribution
            genre_counts = df['genre'].value_counts()
            print(f"🎵 Genres available: {len(genre_counts)}")
            for genre, count in genre_counts.head(10).items():
                print(f"  {genre}: {count:,} songs")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading songs: {e}")
            return False

    def generate_users(self, num_users: int = 10000):
        """Generate diverse user profiles."""
        print(f"👥 Generating {num_users:,} user profiles...")
        
        profile_types = list(self.user_profiles.keys())
        
        for i in range(num_users):
            user_id = f"user_{i+1:06d}"
            
            # Assign random profile type
            profile_type = random.choice(profile_types)
            profile = self.user_profiles[profile_type]
            
            # Generate user characteristics
            user = {
                'user_id': user_id,
                'profile_type': profile_type,
                'preferred_genres': profile['preferred_genres'],
                'genre_weight': profile['weight'],
                'listening_intensity': random.choice(['light', 'moderate', 'heavy']),
                'discovery_rate': random.uniform(0.1, 0.4),  # How often they try new music
                'repeat_rate': random.uniform(0.3, 0.8)      # How often they repeat songs
            }
            
            self.users.append(user)
        
        print(f"✅ Generated {len(self.users):,} users")
        
        # Show profile distribution
        profile_dist = {}
        for user in self.users:
            profile_type = user['profile_type']
            profile_dist[profile_type] = profile_dist.get(profile_type, 0) + 1
        
        print("📊 User profile distribution:")
        for profile, count in profile_dist.items():
            print(f"  {profile}: {count:,} users ({count/len(self.users)*100:.1f}%)")

    def generate_listening_sessions(self, target_records: int = 500000):
        """Generate realistic listening sessions."""
        print(f"🎧 Generating {target_records:,} listening records...")
        
        if not self.songs:
            print("❌ No songs loaded. Please load songs first.")
            return
        
        # Group songs by genre for efficient selection
        songs_by_genre = {}
        for song in self.songs:
            genre = song['genre']
            if genre not in songs_by_genre:
                songs_by_genre[genre] = []
            songs_by_genre[genre].append(song)
        
        # Generate listening records
        records_per_user = target_records // len(self.users)
        
        for user_idx, user in enumerate(self.users):
            user_records = self.generate_user_listening_history(
                user, songs_by_genre, records_per_user
            )
            self.listening_history.extend(user_records)
            
            if (user_idx + 1) % 1000 == 0:
                print(f"  📈 Progress: {user_idx + 1:,}/{len(self.users):,} users processed")
        
        print(f"✅ Generated {len(self.listening_history):,} listening records")

    def generate_user_listening_history(self, user: Dict, songs_by_genre: Dict, target_records: int) -> List[Dict]:
        """Generate listening history for a single user."""
        user_records = []
        
        # Determine listening intensity
        intensity_multiplier = {
            'light': 0.5,
            'moderate': 1.0,
            'heavy': 2.0
        }
        
        actual_records = int(target_records * intensity_multiplier[user['listening_intensity']])
        
        # Generate listening sessions over the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        for _ in range(actual_records):
            # Select song based on user preferences
            song = self.select_song_for_user(user, songs_by_genre)
            
            if song:
                # Generate realistic listening data
                listen_count = self.generate_listen_count(user, song)
                listen_date = self.generate_random_date(start_date, end_date)
                
                record = {
                    'user_id': user['user_id'],
                    'track_name': song['track_name'],
                    'artist': song['artist'],
                    'listen_count': listen_count,
                    'last_listened': listen_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                user_records.append(record)
        
        return user_records

    def select_song_for_user(self, user: Dict, songs_by_genre: Dict) -> Dict:
        """Select a song based on user preferences."""
        # Diverse listeners choose randomly
        if user['profile_type'] == 'diverse_listener':
            return random.choice(self.songs)
        
        # Preference-based selection
        if random.random() < user['genre_weight'] and user['preferred_genres']:
            # Select from preferred genres
            available_genres = [g for g in user['preferred_genres'] if g in songs_by_genre]
            if available_genres:
                genre = random.choice(available_genres)
                return random.choice(songs_by_genre[genre])
        
        # Discovery mode - try something new
        return random.choice(self.songs)

    def generate_listen_count(self, user: Dict, song: Dict) -> int:
        """Generate realistic listen count based on user behavior and song popularity."""
        base_count = 1
        
        # Factor in song popularity
        popularity_factor = song.get('popularity_score', 50) / 100
        
        # Factor in user repeat behavior
        repeat_factor = user['repeat_rate']
        
        # Generate count with some randomness
        max_count = int(base_count * (1 + popularity_factor * 10) * (1 + repeat_factor * 5))
        return random.randint(1, max(1, max_count))

    def generate_random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate a random date between start and end."""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        random_hours = random.randrange(24)
        random_minutes = random.randrange(60)
        
        return start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)

    def save_to_csv(self, filename: str = "massive_user_listening_history.csv"):
        """Save listening history to CSV."""
        if not self.listening_history:
            print("❌ No listening history to save")
            return None
        
        df = pd.DataFrame(self.listening_history)
        filepath = f"data/sample/{filename}"
        df.to_csv(filepath, index=False)
        
        print(f"\n💾 Saved {len(self.listening_history):,} listening records to {filepath}")
        
        # Show statistics
        print("📊 Listening history statistics:")
        print(f"  Unique users: {df['user_id'].nunique():,}")
        print(f"  Unique songs: {df['track_name'].nunique():,}")
        print(f"  Total listen events: {len(df):,}")
        print(f"  Average listens per user: {len(df) / df['user_id'].nunique():.1f}")
        
        return filepath

def main():
    """Main function to generate massive listening history."""
    try:
        generator = MassiveListeningHistoryGenerator()
        
        # Load songs from database
        if not generator.load_songs_from_database():
            print("❌ Failed to load songs. Make sure the database has songs.")
            return False
        
        # Generate users
        generator.generate_users(num_users=10000)
        
        # Generate listening sessions
        generator.generate_listening_sessions(target_records=500000)
        
        # Save to CSV
        filepath = generator.save_to_csv()
        
        print(f"\n🎉 SUCCESS! Generated massive listening history!")
        print(f"📁 File saved: {filepath}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
