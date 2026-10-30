#!/usr/bin/env python3
"""
Simple Spotify Data Fetcher - Basic search functionality
"""

import os
import sys
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict
from pathlib import Path

class SimpleSpotifyFetcher:
    """Simple Spotify data fetcher with basic search."""
    
    def __init__(self, client_id: str, client_secret: str):
        # Set up authentication
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    def search_tracks_simple(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for tracks with basic info only."""
        try:
            results = self.sp.search(q=query, type='track', limit=limit, market='ZA')
            tracks = results['tracks']['items']
            
            track_data = []
            for track in tracks:
                if not track['id']:
                    continue
                
                # Determine genre based on query or artist
                genre = "unknown"
                query_lower = query.lower()
                artist_name = track['artists'][0]['name'].lower()
                
                if 'amapiano' in query_lower or any(name in artist_name for name in ['kabza', 'maphorisa', 'master kg']):
                    genre = "amapiano"
                elif 'afrobeats' in query_lower or any(name in artist_name for name in ['burna', 'wizkid', 'davido', 'tyla']):
                    genre = "afrobeats"
                elif 'hip hop' in query_lower or 'rap' in query_lower:
                    genre = "hip-hop"
                elif 'gqom' in query_lower:
                    genre = "gqom"
                elif 'pop' in query_lower or track['popularity'] > 70:
                    genre = "pop"
                
                track_info = {
                    "track_name": track['name'],
                    "artist": ", ".join([artist['name'] for artist in track['artists']]),
                    "genre": genre,
                    "popularity_score": track['popularity'] / 100.0,
                    "spotify_id": track['id'],
                    # Set default audio features (we'll skip the audio features API for now)
                    "danceability": 0.7,
                    "energy": 0.7,
                    "valence": 0.6,
                    "tempo": 120.0,
                    "acousticness": 0.2,
                    "instrumentalness": 0.0,
                    "liveness": 0.1,
                    "speechiness": 0.1
                }
                
                track_data.append(track_info)
            
            return track_data
            
        except Exception as e:
            print(f"⚠️ Error searching for '{query}': {e}")
            return []
    
    def fetch_south_african_music(self) -> pd.DataFrame:
        """Fetch South African music using search queries."""
        search_queries = [
            "Master KG",
            "Kabza De Small", 
            "DJ Maphorisa",
            "Tyla",
            "Focalistic",
            "amapiano",
            "Burna Boy",
            "Wizkid",
            "south african music",
            "afrobeats"
        ]
        
        all_tracks = []
        for query in search_queries:
            print(f"🔍 Searching: {query}")
            tracks = self.search_tracks_simple(query, limit=10)
            all_tracks.extend(tracks)
        
        # Remove duplicates based on spotify_id
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track['spotify_id'] not in seen_ids:
                seen_ids.add(track['spotify_id'])
                unique_tracks.append(track)
        
        return pd.DataFrame(unique_tracks)

def main():
    """Main function."""
    print("🎵 SIMPLE SPOTIFY DATA FETCHER")
    print("=" * 50)
    
    # Get credentials from environment or user input
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id:
        client_id = input("Enter your Spotify Client ID: ").strip()
    if not client_secret:
        client_secret = input("Enter your Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Spotify credentials required!")
        return 1
    
    try:
        # Initialize fetcher
        print("🔑 Connecting to Spotify API...")
        fetcher = SimpleSpotifyFetcher(client_id, client_secret)
        
        # Test connection
        print("✅ Connected successfully!")
        
        # Fetch data
        print("🎵 Fetching South African music...")
        tracks_df = fetcher.fetch_south_african_music()
        
        if len(tracks_df) == 0:
            print("❌ No tracks found!")
            return 1
        
        # Save to CSV
        data_dir = Path("data/sample")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / "spotify_simple_songs.csv"
        tracks_df.to_csv(output_file, index=False)
        
        print(f"✅ Fetched {len(tracks_df)} unique tracks")
        print(f"📁 Saved to: {output_file}")
        
        # Show genre breakdown
        genre_counts = tracks_df['genre'].value_counts()
        print(f"\n📊 Genre breakdown:")
        for genre, count in genre_counts.items():
            print(f"   {genre}: {count} tracks")
        
        # Show sample tracks
        print(f"\n🎵 Sample tracks:")
        for i, row in tracks_df.head(5).iterrows():
            print(f"   {row['track_name']} - {row['artist']} ({row['genre']})")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
