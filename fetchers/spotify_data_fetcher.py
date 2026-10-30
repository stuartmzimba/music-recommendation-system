#!/usr/bin/env python3
"""
Spotify Data Fetcher - Get real music data from Spotify API
"""

import os
import sys
import json
import pandas as pd
import requests
import base64
from typing import List, Dict, Optional
from pathlib import Path

class SpotifyDataFetcher:
    """Fetch music data from Spotify Web API."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
        
    def get_access_token(self) -> str:
        """Get access token for Spotify API."""
        auth_url = "https://accounts.spotify.com/api/token"
        
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        return self.access_token
    
    def search_tracks(self, query: str, limit: int = 50, market: str = "ZA") -> List[Dict]:
        """Search for tracks on Spotify."""
        if not self.access_token:
            self.get_access_token()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        params = {
            "q": query,
            "type": "track",
            "limit": limit,
            "market": market  # ZA = South Africa
        }
        
        response = requests.get(f"{self.base_url}/search", headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()["tracks"]["items"]
    
    def get_audio_features(self, track_ids: List[str]) -> List[Dict]:
        """Get audio features for tracks."""
        if not self.access_token:
            self.get_access_token()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Spotify allows max 100 IDs per request
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch_ids = track_ids[i:i+100]
            ids_param = ",".join(batch_ids)
            
            response = requests.get(
                f"{self.base_url}/audio-features",
                headers=headers,
                params={"ids": ids_param}
            )
            response.raise_for_status()
            
            features = response.json()["audio_features"]
            all_features.extend([f for f in features if f])  # Filter out None values
        
        return all_features
    
    def fetch_genre_tracks(self, genre_queries: List[str], tracks_per_genre: int = 20) -> pd.DataFrame:
        """Fetch tracks for specific genres."""
        all_tracks = []
        
        for genre in genre_queries:
            print(f"🎵 Fetching {genre} tracks...")
            
            # Search for tracks in this genre
            tracks = self.search_tracks(f"genre:{genre}", limit=tracks_per_genre)
            
            # Get track IDs for audio features
            track_ids = [track["id"] for track in tracks]
            audio_features = self.get_audio_features(track_ids)
            
            # Create feature lookup
            features_dict = {f["id"]: f for f in audio_features}
            
            # Process tracks
            for track in tracks:
                track_id = track["id"]
                features = features_dict.get(track_id, {})
                
                track_data = {
                    "track_name": track["name"],
                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                    "genre": genre,
                    "popularity_score": track["popularity"] / 100.0,  # Convert to 0-1 scale
                    "spotify_id": track_id,
                    "danceability": features.get("danceability"),
                    "energy": features.get("energy"),
                    "valence": features.get("valence"),
                    "tempo": features.get("tempo"),
                    "acousticness": features.get("acousticness"),
                    "instrumentalness": features.get("instrumentalness"),
                    "liveness": features.get("liveness"),
                    "speechiness": features.get("speechiness")
                }
                
                all_tracks.append(track_data)
        
        return pd.DataFrame(all_tracks)
    
    def fetch_south_african_music(self) -> pd.DataFrame:
        """Fetch popular South African music."""
        sa_queries = [
            "amapiano",
            "afrobeats south africa",
            "gqom",
            "south african hip hop",
            "kwaito",
            "maskandi",
            "south african jazz"
        ]
        
        return self.fetch_genre_tracks(sa_queries, tracks_per_genre=30)
    
    def fetch_international_hits(self) -> pd.DataFrame:
        """Fetch international hit songs."""
        international_queries = [
            "pop",
            "hip hop",
            "rock",
            "electronic",
            "r&b",
            "indie",
            "country"
        ]
        
        return self.fetch_genre_tracks(international_queries, tracks_per_genre=25)

def main():
    """Main function to fetch Spotify data."""
    print("🎵 SPOTIFY DATA FETCHER")
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
        fetcher = SpotifyDataFetcher(client_id, client_secret)
        
        # Fetch data
        print("🌍 Fetching South African music...")
        sa_music = fetcher.fetch_south_african_music()
        
        print("🌎 Fetching international hits...")
        international_music = fetcher.fetch_international_hits()
        
        # Save to CSV files
        data_dir = Path("data/sample")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        sa_music.to_csv(data_dir / "spotify_south_african_songs.csv", index=False)
        international_music.to_csv(data_dir / "spotify_international_songs.csv", index=False)
        
        print(f"✅ Saved {len(sa_music)} South African tracks")
        print(f"✅ Saved {len(international_music)} international tracks")
        print(f"📁 Files saved to: {data_dir}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error fetching Spotify data: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
