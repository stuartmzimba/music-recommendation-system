#!/usr/bin/env python3
"""
Enhanced Spotify Data Fetcher for 50,000+ Songs with Multiple Genres
Fetches a massive dataset from Spotify with diverse genres and artists.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import random
from typing import List, Dict, Set
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MassiveSpotifyFetcher:
    def __init__(self):
        """Initialize Spotify client with credentials."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
        
        # Initialize Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Track unique songs to avoid duplicates
        self.unique_tracks: Set[str] = set()
        self.all_songs: List[Dict] = []
        
        # Expanded genre categories with search terms
        self.genre_searches = {
            # African Music
            'Amapiano': ['amapiano', 'kabza de small', 'dj maphorisa', 'focalistic', 'mas musiq'],
            'Afrobeats': ['afrobeats', 'burna boy', 'wizkid', 'davido', 'tiwa savage', 'yemi alade'],
            'Afrohouse': ['afrohouse', 'black coffee', 'culoe de song', 'atjazz'],
            'Gqom': ['gqom', 'distruction boyz', 'dj tira', 'babes wodumo'],
            'Kwaito': ['kwaito', 'arthur mafokate', 'mandoza', 'zola'],
            'Bongo Flava': ['bongo flava', 'diamond platnumz', 'ali kiba', 'harmonize'],
            
            # Global Pop & Mainstream
            'Pop': ['pop hits', 'taylor swift', 'dua lipa', 'ariana grande', 'ed sheeran'],
            'Hip-Hop': ['hip hop', 'drake', 'kendrick lamar', 'j cole', 'travis scott'],
            'R&B': ['r&b', 'the weeknd', 'sza', 'frank ocean', 'daniel caesar'],
            'Electronic': ['electronic', 'calvin harris', 'david guetta', 'martin garrix'],
            'Dance': ['dance music', 'swedish house mafia', 'tiesto', 'deadmau5'],
            
            # Rock & Alternative
            'Rock': ['rock music', 'imagine dragons', 'coldplay', 'maroon 5'],
            'Alternative': ['alternative rock', 'arctic monkeys', 'tame impala', 'radiohead'],
            'Indie': ['indie music', 'vampire weekend', 'foster the people', 'mgmt'],
            
            # Latin Music
            'Reggaeton': ['reggaeton', 'bad bunny', 'j balvin', 'ozuna', 'daddy yankee'],
            'Latin Pop': ['latin pop', 'shakira', 'jesse joy', 'manu chao'],
            'Salsa': ['salsa music', 'marc anthony', 'la santa cecilia'],
            
            # Jazz & Soul
            'Jazz': ['jazz music', 'miles davis', 'john coltrane', 'billie holiday'],
            'Neo-Soul': ['neo soul', 'erykah badu', 'lauryn hill', 'd angelo'],
            'Soul': ['soul music', 'stevie wonder', 'aretha franklin', 'otis redding'],
            'Funk': ['funk music', 'james brown', 'parliament funkadelic', 'prince'],
            
            # World Music
            'Reggae': ['reggae', 'bob marley', 'jimmy cliff', 'burning spear'],
            'Dancehall': ['dancehall', 'sean paul', 'shaggy', 'beenie man'],
            'Country': ['country music', 'taylor swift country', 'keith urban', 'carrie underwood'],
            'Folk': ['folk music', 'bob dylan', 'joni mitchell', 'neil young'],
            
            # Indian & Asian
            'Bollywood': ['bollywood', 'arijit singh', 'shreya ghoshal', 'a r rahman'],
            'K-Pop': ['k-pop', 'bts', 'blackpink', 'twice', 'stray kids'],
            'J-Pop': ['j-pop', 'utada hikaru', 'ayumi hamasaki'],
            
            # Classical & Instrumental
            'Classical': ['classical music', 'beethoven', 'mozart', 'bach'],
            'Instrumental': ['instrumental music', 'ludovico einaudi', 'max richter'],
            
            # Gospel & Spiritual
            'Gospel': ['gospel music', 'kirk franklin', 'yolanda adams', 'donnie mcclurkin'],
            'Christian': ['christian music', 'hillsong', 'chris tomlin', 'lauren daigle'],
            
            # Blues & Country
            'Blues': ['blues music', 'bb king', 'muddy waters', 'eric clapton'],
            'Bluegrass': ['bluegrass', 'alison krauss', 'chris thile'],
            
            # Electronic Subgenres
            'House': ['house music', 'daft punk', 'disclosure', 'duke dumont'],
            'Techno': ['techno music', 'carl cox', 'richie hawtin', 'adam beyer'],
            'Dubstep': ['dubstep', 'skrillex', 'bassnectar', 'flux pavilion'],
            'Trance': ['trance music', 'armin van buuren', 'above beyond', 'paul van dyk']
        }

    def search_tracks_by_genre(self, genre: str, search_terms: List[str], target_count: int = 1000) -> List[Dict]:
        """Search for tracks in a specific genre."""
        print(f"\n🎵 Fetching {genre} tracks...")
        genre_tracks = []
        
        for search_term in search_terms:
            if len(genre_tracks) >= target_count:
                break
                
            try:
                # Search for tracks
                results = self.sp.search(q=search_term, type='track', limit=50, market='US')
                
                for track in results['tracks']['items']:
                    if len(genre_tracks) >= target_count:
                        break
                    
                    # Create unique identifier
                    track_id = f"{track['name']}_{track['artists'][0]['name']}"
                    
                    if track_id not in self.unique_tracks:
                        self.unique_tracks.add(track_id)
                        
                        # Get audio features
                        audio_features = self.get_audio_features(track['id'])
                        
                        song_data = {
                            'track_name': track['name'],
                            'artist': track['artists'][0]['name'],
                            'genre': genre,
                            'popularity_score': track['popularity'],
                            'spotify_id': track['id'],
                            'danceability': audio_features.get('danceability', 0.5),
                            'energy': audio_features.get('energy', 0.5),
                            'valence': audio_features.get('valence', 0.5),
                            'tempo': audio_features.get('tempo', 120),
                            'acousticness': audio_features.get('acousticness', 0.5),
                            'instrumentalness': audio_features.get('instrumentalness', 0.5),
                            'liveness': audio_features.get('liveness', 0.5),
                            'speechiness': audio_features.get('speechiness', 0.5)
                        }
                        
                        genre_tracks.append(song_data)
                        
                        if len(genre_tracks) % 50 == 0:
                            print(f"  📊 {genre}: {len(genre_tracks)} tracks fetched...")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ⚠️ Error searching '{search_term}': {e}")
                time.sleep(1)
                continue
        
        print(f"  ✅ {genre}: {len(genre_tracks)} tracks collected")
        return genre_tracks

    def get_audio_features(self, track_id: str) -> Dict:
        """Get audio features for a track."""
        try:
            features = self.sp.audio_features([track_id])[0]
            return features if features else {}
        except Exception as e:
            print(f"  ⚠️ Error getting audio features: {e}")
            return {}

    def fetch_massive_dataset(self, target_total: int = 50000) -> List[Dict]:
        """Fetch a massive dataset of songs across all genres."""
        print(f"🚀 Starting massive Spotify data fetch for {target_total:,} songs...")
        print(f"📊 Targeting {len(self.genre_searches)} genres")
        
        # Calculate target per genre
        target_per_genre = target_total // len(self.genre_searches)
        print(f"🎯 Target per genre: ~{target_per_genre} songs")
        
        all_tracks = []
        
        for genre, search_terms in self.genre_searches.items():
            genre_tracks = self.search_tracks_by_genre(genre, search_terms, target_per_genre)
            all_tracks.extend(genre_tracks)
            
            print(f"📈 Total progress: {len(all_tracks):,}/{target_total:,} songs ({len(all_tracks)/target_total*100:.1f}%)")
            
            # Save intermediate results every 5 genres
            if len(all_tracks) % (target_per_genre * 5) == 0:
                self.save_intermediate_results(all_tracks)
        
        print(f"\n🎉 Massive fetch complete! Total unique songs: {len(all_tracks):,}")
        return all_tracks

    def save_intermediate_results(self, tracks: List[Dict]):
        """Save intermediate results to prevent data loss."""
        df = pd.DataFrame(tracks)
        filename = f"data/sample/spotify_massive_intermediate_{len(tracks)}.csv"
        df.to_csv(filename, index=False)
        print(f"💾 Intermediate save: {filename}")

    def save_to_csv(self, tracks: List[Dict], filename: str = "spotify_massive_songs.csv"):
        """Save tracks to CSV file."""
        df = pd.DataFrame(tracks)
        filepath = f"data/sample/{filename}"
        df.to_csv(filepath, index=False)
        
        print(f"\n💾 Saved {len(tracks):,} songs to {filepath}")
        print(f"📊 Genres distribution:")
        genre_counts = df['genre'].value_counts()
        for genre, count in genre_counts.items():
            print(f"  {genre}: {count:,} songs")
        
        return filepath

def main():
    """Main function to fetch massive Spotify dataset."""
    try:
        fetcher = MassiveSpotifyFetcher()
        
        # Fetch 50,000 songs
        tracks = fetcher.fetch_massive_dataset(target_total=50000)
        
        # Save to CSV
        filepath = fetcher.save_to_csv(tracks)
        
        print(f"\n🎉 SUCCESS! Fetched {len(tracks):,} unique songs with {len(fetcher.genre_searches)} genres!")
        print(f"📁 File saved: {filepath}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
