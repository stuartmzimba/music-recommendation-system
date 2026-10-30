#!/usr/bin/env python3
"""
Easy Spotify Data Fetcher using Spotipy library
"""

import os
import sys
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict
from pathlib import Path

class EasySpotifyFetcher:
    """Easy Spotify data fetcher using spotipy."""
    
    def __init__(self, client_id: str, client_secret: str):
        # Set up authentication
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get tracks from a Spotify playlist."""
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                track = item['track']
                if track and track['id']:  # Skip None tracks
                    tracks.append(track)
            
            # Get next page if available
            results = self.sp.next(results) if results['next'] else None
        
        return tracks
    
    def search_and_get_tracks(self, queries: List[str], limit_per_query: int = 20) -> List[Dict]:
        """Search for tracks and return results."""
        all_tracks = []
        
        for query in queries:
            print(f"🔍 Searching: {query}")
            results = self.sp.search(q=query, type='track', limit=limit_per_query, market='ZA')
            all_tracks.extend(results['tracks']['items'])
        
        return all_tracks
    
    def tracks_to_dataframe(self, tracks: List[Dict]) -> pd.DataFrame:
        """Convert Spotify tracks to DataFrame."""
        track_data = []
        
        # Get track IDs for audio features
        track_ids = [track['id'] for track in tracks if track['id']]
        
        # Get audio features in batches
        audio_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = self.sp.audio_features(batch)
            audio_features.extend([f for f in features if f])
        
        # Create feature lookup
        features_dict = {f['id']: f for f in audio_features}
        
        for track in tracks:
            if not track['id']:
                continue
                
            features = features_dict.get(track['id'], {})
            
            # Determine genre (simplified)
            genre = "unknown"
            if any(keyword in track['name'].lower() for keyword in ['amapiano', 'piano']):
                genre = "amapiano"
            elif any(keyword in track['artists'][0]['name'].lower() for keyword in ['burna', 'wizkid', 'davido']):
                genre = "afrobeats"
            elif track['popularity'] > 70:
                genre = "pop"
            
            track_info = {
                "track_name": track['name'],
                "artist": ", ".join([artist['name'] for artist in track['artists']]),
                "genre": genre,
                "popularity_score": track['popularity'] / 100.0,
                "spotify_id": track['id'],
                "danceability": features.get('danceability'),
                "energy": features.get('energy'),
                "valence": features.get('valence'),
                "tempo": features.get('tempo'),
                "acousticness": features.get('acousticness'),
                "instrumentalness": features.get('instrumentalness'),
                "liveness": features.get('liveness'),
                "speechiness": features.get('speechiness')
            }
            
            track_data.append(track_info)
        
        return pd.DataFrame(track_data)
    
    def fetch_south_african_playlists(self) -> pd.DataFrame:
        """Fetch tracks from popular South African playlists."""
        # Popular SA playlists (you can find these on Spotify)
        sa_playlists = [
            "37i9dQZF1DX7YCknf2jT6s",  # Amapiano Grooves
            "37i9dQZF1DWYmmr74INdgF",  # Afro Hits
            "37i9dQZF1DX0XUfTFmNBRM",  # Mzansi Hip Hop
        ]
        
        all_tracks = []
        for playlist_id in sa_playlists:
            try:
                print(f"📋 Fetching playlist: {playlist_id}")
                tracks = self.get_playlist_tracks(playlist_id)
                all_tracks.extend(tracks)
            except Exception as e:
                print(f"⚠️ Error fetching playlist {playlist_id}: {e}")
        
        return self.tracks_to_dataframe(all_tracks)
    
    def fetch_by_search_terms(self) -> pd.DataFrame:
        """Fetch tracks by searching for specific terms."""
        search_queries = [
            "amapiano south africa",
            "Master KG",
            "Kabza De Small", 
            "DJ Maphorisa",
            "Burna Boy afrobeats",
            "Wizkid",
            "Focalistic",
            "Tyla Water",
            "south african hip hop",
            "gqom music",
            "kwaito",
            "maskandi"
        ]
        
        tracks = self.search_and_get_tracks(search_queries, limit_per_query=15)
        return self.tracks_to_dataframe(tracks)

def main():
    """Main function."""
    print("🎵 EASY SPOTIFY DATA FETCHER")
    print("=" * 50)
    
    # Get credentials
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id:
        print("Set SPOTIFY_CLIENT_ID environment variable or enter manually:")
        client_id = input("Spotify Client ID: ").strip()
    
    if not client_secret:
        print("Set SPOTIFY_CLIENT_SECRET environment variable or enter manually:")
        client_secret = input("Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Spotify credentials required!")
        print("\n📝 To get credentials:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create a new app")
        print("3. Copy Client ID and Client Secret")
        return 1
    
    try:
        # Initialize fetcher
        fetcher = EasySpotifyFetcher(client_id, client_secret)
        
        # Fetch data using different methods
        print("🎵 Method 1: Fetching from playlists...")
        playlist_tracks = fetcher.fetch_south_african_playlists()
        
        print("🔍 Method 2: Fetching by search terms...")
        search_tracks = fetcher.fetch_by_search_terms()
        
        # Combine and remove duplicates
        all_tracks = pd.concat([playlist_tracks, search_tracks], ignore_index=True)
        all_tracks = all_tracks.drop_duplicates(subset=['spotify_id'], keep='first')
        
        # Save to CSV
        data_dir = Path("data/sample")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / "spotify_fetched_songs.csv"
        all_tracks.to_csv(output_file, index=False)
        
        print(f"✅ Fetched {len(all_tracks)} unique tracks")
        print(f"📁 Saved to: {output_file}")
        
        # Show genre breakdown
        genre_counts = all_tracks['genre'].value_counts()
        print(f"\n📊 Genre breakdown:")
        for genre, count in genre_counts.items():
            print(f"   {genre}: {count} tracks")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
