#!/usr/bin/env python3
"""
Detailed test of API genre endpoints and recommendations.
"""

import json
from urllib.request import urlopen, Request

def test_genres_api():
    """Test the genres API endpoint."""
    print("🌐 Testing Genres API Endpoint")
    print("=" * 40)
    
    try:
        url = "http://localhost:8001/api/v1/genres"
        with urlopen(url) as response:
            genres = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ API returned {len(genres)} genres")
            print(f"📋 All available genres:")
            
            # Sort genres alphabetically for better readability
            sorted_genres = sorted(genres)
            
            for i, genre in enumerate(sorted_genres, 1):
                print(f"  {i:2d}. {genre}")
            
            return sorted_genres
    
    except Exception as e:
        print(f"❌ API Error: {e}")
        return []

def test_genre_specific_recommendations():
    """Test genre-specific recommendations."""
    print(f"\n🎯 Testing Genre-Specific Recommendations")
    print("=" * 50)
    
    # Test key genres
    test_genres = ['Amapiano', 'Pop', 'Hip-Hop', 'Electronic', 'Rock', 'Jazz']
    
    for genre in test_genres:
        print(f"\n🎵 Testing {genre} Recommendations:")
        
        url = "http://localhost:8001/api/v1/recommend"
        data = {
            "basket": [],
            "genres": [genre],
            "top_k": 5
        }
        
        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
            
            with urlopen(req) as response:
                recommendations = json.loads(response.read().decode('utf-8'))
                
                if recommendations:
                    print(f"  ✅ Got {len(recommendations)} recommendations:")
                    
                    genre_matches = 0
                    for i, rec in enumerate(recommendations, 1):
                        track = rec.get('track_name', 'Unknown')
                        artist = rec.get('artist', 'Unknown')
                        rec_genre = rec.get('genre', 'Unknown')
                        method = rec.get('reason', 'Unknown')
                        score = rec.get('score', 0)
                        
                        genre_match = "✅" if rec_genre == genre else "⚠️"
                        if rec_genre == genre:
                            genre_matches += 1
                        
                        print(f"    {i}. {track} by {artist}")
                        print(f"       Genre: {rec_genre} {genre_match} | Method: {method} | Score: {score:.3f}")
                    
                    accuracy = (genre_matches / len(recommendations)) * 100
                    print(f"  📊 Genre accuracy: {genre_matches}/{len(recommendations)} ({accuracy:.1f}%)")
                else:
                    print(f"  ❌ No recommendations returned")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_popular_songs_by_genre():
    """Test popular songs filtering by genre."""
    print(f"\n🏆 Testing Popular Songs by Genre")
    print("=" * 40)
    
    test_genres = ['Amapiano', 'Pop', 'Hip-Hop', 'K-Pop']
    
    for genre in test_genres:
        print(f"\n🎵 Popular {genre} Songs:")
        
        try:
            url = f"http://localhost:8001/api/v1/popular?limit=5&genre={genre}"
            with urlopen(url) as response:
                songs = json.loads(response.read().decode('utf-8'))
                
                if songs:
                    print(f"  ✅ Got {len(songs)} popular songs:")
                    
                    for i, song in enumerate(songs, 1):
                        track = song.get('track_name', 'Unknown')
                        artist = song.get('artist', 'Unknown')
                        song_genre = song.get('genre', 'Unknown')
                        popularity = song.get('popularity_score', 0)
                        
                        genre_match = "✅" if song_genre == genre else "⚠️"
                        print(f"    {i}. {track} by {artist}")
                        print(f"       Genre: {song_genre} {genre_match} | Popularity: {popularity}")
                else:
                    print(f"  ❌ No popular songs found for {genre}")
        
        except Exception as e:
            print(f"  ❌ Error testing {genre}: {e}")

def test_amapiano_authenticity():
    """Detailed test of Amapiano authenticity."""
    print(f"\n🇿🇦 Detailed Amapiano Authenticity Test")
    print("=" * 45)
    
    # Test Amapiano recommendations
    url = "http://localhost:8001/api/v1/recommend"
    data = {
        "basket": [],
        "genres": ["Amapiano"],
        "top_k": 10
    }
    
    try:
        req = Request(url)
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
        
        with urlopen(req) as response:
            recommendations = json.loads(response.read().decode('utf-8'))
            
            print(f"🎵 Amapiano Recommendations Analysis:")
            
            authentic_artists = {
                'kabza de small', 'dj maphorisa', 'focalistic', 'uncle waffles',
                'major league djz', 'mas musiq', 'de mthuda', 'josiah de disciple',
                'vigro deep', 'mellow and sleazy', 'wanitwa mos', 'tito m',
                'snow deep', 'skyface sdw', 'mluusician', 'bantwanas',
                'titom', 'yuppe', 'pcee', 'eemoh', 'royal musiq'
            }
            
            authentic_count = 0
            for i, rec in enumerate(recommendations, 1):
                track = rec.get('track_name', 'Unknown')
                artist = rec.get('artist', 'Unknown')
                method = rec.get('reason', 'Unknown')
                score = rec.get('score', 0)
                
                is_authentic = any(auth_artist in artist.lower() for auth_artist in authentic_artists)
                status = "✅" if is_authentic else "⚠️"
                
                if is_authentic:
                    authentic_count += 1
                
                print(f"  {i:2d}. {status} {track}")
                print(f"      Artist: {artist}")
                print(f"      Method: {method} | Score: {score:.3f}")
            
            if recommendations:
                authenticity_rate = (authentic_count / len(recommendations)) * 100
                print(f"\n📊 Authenticity Summary:")
                print(f"  • Total recommendations: {len(recommendations)}")
                print(f"  • Authentic Amapiano: {authentic_count}")
                print(f"  • Authenticity rate: {authenticity_rate:.1f}%")
                
                if authenticity_rate >= 80:
                    print(f"  ✅ Excellent authenticity!")
                elif authenticity_rate >= 60:
                    print(f"  ⚠️ Good authenticity, some improvements possible")
                else:
                    print(f"  ❌ Low authenticity, needs improvement")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🧪 Detailed API Genre and Filter Testing")
    print("=" * 50)
    
    # Test genres API
    genres = test_genres_api()
    
    # Test genre-specific recommendations
    test_genre_specific_recommendations()
    
    # Test popular songs by genre
    test_popular_songs_by_genre()
    
    # Test Amapiano authenticity
    test_amapiano_authenticity()
    
    print(f"\n🎉 Detailed Testing Complete!")
    print("=" * 35)
    
    print(f"\n📊 Key Findings:")
    print("  • Genre API endpoint functionality")
    print("  • Genre-specific recommendation accuracy")
    print("  • Popular songs filtering by genre")
    print("  • Amapiano authenticity verification")

if __name__ == "__main__":
    main()
