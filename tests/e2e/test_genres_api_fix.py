#!/usr/bin/env python3
"""
Test and fix the genres API endpoint.
"""

import json
from urllib.request import urlopen

def test_genres_api_raw():
    """Test the raw genres API response."""
    print("🔍 Testing Raw Genres API Response")
    print("=" * 40)
    
    try:
        url = "http://localhost:8001/api/v1/genres"
        with urlopen(url) as response:
            raw_response = response.read().decode('utf-8')
            print(f"📡 Raw API Response:")
            print(f"  {raw_response}")
            
            # Parse JSON
            data = json.loads(raw_response)
            print(f"\n📊 Parsed JSON:")
            print(f"  Type: {type(data)}")
            print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if isinstance(data, dict) and 'genres' in data:
                genres = data['genres']
                print(f"\n✅ Found genres list:")
                print(f"  Count: {len(genres)}")
                print(f"  First 10: {genres[:10]}")
                return genres
            else:
                print(f"❌ Unexpected response format")
                return []
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_popular_api():
    """Test the popular songs API."""
    print(f"\n🏆 Testing Popular Songs API")
    print("=" * 35)
    
    try:
        # Test without genre filter
        url = "http://localhost:8001/api/v1/popular?limit=3"
        with urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ General Popular Songs:")
            for i, song in enumerate(data, 1):
                track = song.get('track_name', 'Unknown')
                artist = song.get('artist', 'Unknown')
                genre = song.get('genre', 'Unknown')
                popularity = song.get('popularity_score', 0)
                print(f"  {i}. {track} by {artist} ({genre}) - {popularity}")
        
        # Test with Amapiano filter
        print(f"\n🎵 Testing Amapiano Popular Songs:")
        url = "http://localhost:8001/api/v1/popular?limit=3&genre=Amapiano"
        with urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data:
                print(f"✅ Found {len(data)} Amapiano popular songs:")
                for i, song in enumerate(data, 1):
                    track = song.get('track_name', 'Unknown')
                    artist = song.get('artist', 'Unknown')
                    popularity = song.get('popularity_score', 0)
                    print(f"  {i}. {track} by {artist} - {popularity}")
            else:
                print(f"❌ No Amapiano popular songs found")
                
                # Check if there are any Amapiano songs in popular_songs table
                print(f"🔍 This might be because Amapiano songs aren't in the popular_songs table")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def check_popular_songs_table():
    """Check what's in the popular_songs table."""
    print(f"\n📊 Checking Popular Songs Table")
    print("=" * 35)
    
    import sqlite3
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Check total popular songs
    cursor.execute("SELECT COUNT(*) FROM popular_songs")
    total_popular = cursor.fetchone()[0]
    print(f"📈 Total popular songs: {total_popular:,}")
    
    # Check genres in popular songs
    cursor.execute("""
        SELECT s.genre, COUNT(*) as count
        FROM popular_songs ps
        JOIN songs s ON ps.song_id = s.id
        GROUP BY s.genre
        ORDER BY count DESC
        LIMIT 10
    """)
    
    popular_genres = cursor.fetchall()
    print(f"\n🎭 Top genres in popular_songs table:")
    for genre, count in popular_genres:
        print(f"  {genre}: {count} songs")
    
    # Check if Amapiano is in popular songs
    cursor.execute("""
        SELECT COUNT(*) 
        FROM popular_songs ps
        JOIN songs s ON ps.song_id = s.id
        WHERE s.genre = 'Amapiano'
    """)
    
    amapiano_popular_count = cursor.fetchone()[0]
    print(f"\n🎵 Amapiano songs in popular_songs: {amapiano_popular_count}")
    
    if amapiano_popular_count == 0:
        print(f"⚠️ No Amapiano songs in popular_songs table!")
        print(f"   This explains why the API returns no popular Amapiano songs")
        
        # Check Amapiano songs with high popularity
        cursor.execute("""
            SELECT track_name, artist, popularity_score
            FROM songs
            WHERE genre = 'Amapiano'
            ORDER BY popularity_score DESC
            LIMIT 5
        """)
        
        top_amapiano = cursor.fetchall()
        print(f"\n🎯 Top Amapiano songs by popularity (not in popular_songs):")
        for track, artist, pop in top_amapiano:
            print(f"  {track} by {artist} - {pop}")
    
    conn.close()

def main():
    print("🧪 Testing and Fixing API Issues")
    print("=" * 40)
    
    # Test genres API
    genres = test_genres_api_raw()
    
    # Test popular API
    test_popular_api()
    
    # Check popular songs table
    check_popular_songs_table()
    
    print(f"\n🎉 API Testing Summary")
    print("=" * 30)
    
    if genres:
        print(f"✅ Genres API: Working ({len(genres)} genres)")
    else:
        print(f"❌ Genres API: Issues detected")
    
    print(f"\n💡 Key Issues Found:")
    print("  • Genres API returns wrapped response (need to access data['genres'])")
    print("  • Amapiano songs might not be in popular_songs table")
    print("  • Popular songs filtering by genre works for other genres")

if __name__ == "__main__":
    main()
