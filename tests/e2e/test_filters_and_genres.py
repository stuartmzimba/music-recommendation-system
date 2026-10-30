#!/usr/bin/env python3
"""
Test popularity filters and genre assignments to ensure everything is working correctly.
"""

import sqlite3
import json
from urllib.request import urlopen, Request
from collections import defaultdict

def test_popularity_filters():
    """Test if popularity filtering is working correctly."""
    print("🔍 Testing Popularity Filters")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Test popularity distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN popularity_score >= 90 THEN 'Very High (90-100)'
                WHEN popularity_score >= 70 THEN 'High (70-89)'
                WHEN popularity_score >= 50 THEN 'Medium (50-69)'
                WHEN popularity_score >= 30 THEN 'Low (30-49)'
                ELSE 'Very Low (0-29)'
            END as popularity_range,
            COUNT(*) as count,
            AVG(popularity_score) as avg_score
        FROM songs
        GROUP BY 
            CASE 
                WHEN popularity_score >= 90 THEN 'Very High (90-100)'
                WHEN popularity_score >= 70 THEN 'High (70-89)'
                WHEN popularity_score >= 50 THEN 'Medium (50-69)'
                WHEN popularity_score >= 30 THEN 'Low (30-49)'
                ELSE 'Very Low (0-29)'
            END
        ORDER BY avg_score DESC
    """)
    
    popularity_ranges = cursor.fetchall()
    
    print("📊 Popularity Distribution:")
    total_songs = sum(count for _, count, _ in popularity_ranges)
    
    for range_name, count, avg_score in popularity_ranges:
        percentage = (count / total_songs) * 100
        print(f"  {range_name}: {count:,} songs ({percentage:.1f}%) - Avg: {avg_score:.1f}")
    
    # Test top popular songs
    print(f"\n🏆 Top 10 Most Popular Songs:")
    cursor.execute("""
        SELECT track_name, artist, genre, popularity_score
        FROM songs
        ORDER BY popularity_score DESC
        LIMIT 10
    """)
    
    top_songs = cursor.fetchall()
    for i, (track, artist, genre, pop) in enumerate(top_songs, 1):
        print(f"  {i:2d}. {track} by {artist} ({genre}) - {pop}")
    
    # Test least popular songs
    print(f"\n📉 Bottom 5 Least Popular Songs:")
    cursor.execute("""
        SELECT track_name, artist, genre, popularity_score
        FROM songs
        WHERE popularity_score > 0
        ORDER BY popularity_score ASC
        LIMIT 5
    """)
    
    bottom_songs = cursor.fetchall()
    for i, (track, artist, genre, pop) in enumerate(bottom_songs, 1):
        print(f"  {i}. {track} by {artist} ({genre}) - {pop}")
    
    conn.close()

def test_api_popularity_filter():
    """Test the API popularity filtering endpoints."""
    print(f"\n🌐 Testing API Popularity Filters")
    print("=" * 40)
    
    # Test popular songs endpoint
    try:
        # Test general popular songs
        url = "http://localhost:8001/api/v1/popular?limit=5"
        with urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ General Popular Songs API (limit=5):")
            for i, song in enumerate(data, 1):
                track = song.get('track_name', 'Unknown')
                artist = song.get('artist', 'Unknown')
                genre = song.get('genre', 'Unknown')
                popularity = song.get('popularity_score', 0)
                print(f"  {i}. {track} by {artist} ({genre}) - {popularity}")
        
        # Test genre-specific popular songs
        test_genres = ['Amapiano', 'Pop', 'Hip-Hop', 'Electronic']
        
        for genre in test_genres:
            url = f"http://localhost:8001/api/v1/popular?limit=3&genre={genre}"
            try:
                with urlopen(url) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    print(f"\n✅ Popular {genre} Songs:")
                    for i, song in enumerate(data, 1):
                        track = song.get('track_name', 'Unknown')
                        artist = song.get('artist', 'Unknown')
                        popularity = song.get('popularity_score', 0)
                        print(f"  {i}. {track} by {artist} - {popularity}")
            except Exception as e:
                print(f"❌ Error testing {genre}: {e}")
    
    except Exception as e:
        print(f"❌ API Error: {e}")

def test_genre_assignments():
    """Test if songs are assigned correct genres."""
    print(f"\n🎭 Testing Genre Assignments")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get all genres and their counts
    cursor.execute("""
        SELECT genre, COUNT(*) as count
        FROM songs
        GROUP BY genre
        ORDER BY count DESC
    """)
    
    genres = cursor.fetchall()
    
    print(f"📊 Genre Distribution ({len(genres)} total genres):")
    total_songs = sum(count for _, count in genres)
    
    for genre, count in genres:
        percentage = (count / total_songs) * 100
        print(f"  {genre}: {count:,} songs ({percentage:.1f}%)")
    
    # Test specific genre accuracy
    print(f"\n🔍 Testing Specific Genre Accuracy:")
    
    # Test Amapiano (should be South African artists)
    print(f"\n🎵 Amapiano Genre Check:")
    cursor.execute("""
        SELECT track_name, artist, popularity_score
        FROM songs
        WHERE genre = 'Amapiano'
        ORDER BY popularity_score DESC
        LIMIT 10
    """)
    
    amapiano_songs = cursor.fetchall()
    print(f"  Top 10 Amapiano songs:")
    
    authentic_amapiano_artists = {
        'kabza de small', 'dj maphorisa', 'focalistic', 'uncle waffles',
        'major league djz', 'mas musiq', 'de mthuda', 'josiah de disciple',
        'vigro deep', 'mellow and sleazy', 'wanitwa mos', 'tito m',
        'snow deep', 'skyface sdw', 'mluusician', 'bantwanas'
    }
    
    authentic_count = 0
    for track, artist, pop in amapiano_songs:
        is_authentic = any(auth_artist in artist.lower() for auth_artist in authentic_amapiano_artists)
        status = "✅" if is_authentic else "⚠️"
        print(f"    {status} {track} by {artist} (pop: {pop})")
        if is_authentic:
            authentic_count += 1
    
    authenticity_rate = (authentic_count / len(amapiano_songs)) * 100
    print(f"  📊 Authenticity rate: {authentic_count}/{len(amapiano_songs)} ({authenticity_rate:.1f}%)")
    
    # Test other genres for obvious misassignments
    test_genre_samples = {
        'Pop': ['taylor swift', 'ariana grande', 'ed sheeran', 'billie eilish'],
        'Hip-Hop': ['drake', 'kendrick lamar', 'j. cole', 'travis scott'],
        'Rock': ['queen', 'the beatles', 'led zeppelin', 'pink floyd'],
        'Electronic': ['calvin harris', 'david guetta', 'skrillex', 'deadmau5'],
        'Jazz': ['miles davis', 'john coltrane', 'ella fitzgerald', 'louis armstrong']
    }
    
    for genre, expected_artists in test_genre_samples.items():
        cursor.execute("""
            SELECT track_name, artist
            FROM songs
            WHERE genre = ?
            ORDER BY popularity_score DESC
            LIMIT 5
        """, (genre,))
        
        genre_songs = cursor.fetchall()
        if genre_songs:
            print(f"\n🎵 {genre} Genre Check:")
            correct_assignments = 0
            
            for track, artist in genre_songs:
                is_expected = any(exp_artist in artist.lower() for exp_artist in expected_artists)
                status = "✅" if is_expected else "❓"
                print(f"    {status} {track} by {artist}")
                if is_expected:
                    correct_assignments += 1
            
            if len(genre_songs) > 0:
                accuracy = (correct_assignments / len(genre_songs)) * 100
                print(f"    📊 Expected artist rate: {correct_assignments}/{len(genre_songs)} ({accuracy:.1f}%)")
    
    conn.close()

def test_genre_api_filter():
    """Test the API genre filtering."""
    print(f"\n🌐 Testing API Genre Filters")
    print("=" * 40)
    
    try:
        # Test genres endpoint
        url = "http://localhost:8001/api/v1/genres"
        with urlopen(url) as response:
            genres = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ Available Genres from API ({len(genres)} total):")
            for i, genre in enumerate(genres[:10], 1):  # Show first 10
                print(f"  {i:2d}. {genre}")
            
            if len(genres) > 10:
                print(f"  ... and {len(genres) - 10} more genres")
        
        # Test genre-specific recommendations
        print(f"\n🎯 Testing Genre-Specific Recommendations:")
        
        test_genres = ['Amapiano', 'Pop', 'Hip-Hop']
        for genre in test_genres:
            url = "http://localhost:8001/api/v1/recommend"
            data = {
                "basket": [],
                "genres": [genre],
                "top_k": 3
            }
            
            try:
                req = Request(url)
                req.add_header('Content-Type', 'application/json')
                req.data = json.dumps(data).encode('utf-8')
                
                with urlopen(req) as response:
                    recommendations = json.loads(response.read().decode('utf-8'))
                    
                    print(f"\n  ✅ {genre} Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        track = rec.get('track_name', 'Unknown')
                        artist = rec.get('artist', 'Unknown')
                        rec_genre = rec.get('genre', 'Unknown')
                        method = rec.get('reason', 'Unknown')
                        
                        genre_match = "✅" if rec_genre == genre else "⚠️"
                        print(f"    {i}. {track} by {artist} ({rec_genre}) {genre_match}")
                        print(f"       Method: {method}")
            
            except Exception as e:
                print(f"    ❌ Error testing {genre} recommendations: {e}")
    
    except Exception as e:
        print(f"❌ API Error: {e}")

def main():
    print("🧪 Testing Popularity Filters and Genre Assignments")
    print("=" * 60)
    
    # Test popularity filters
    test_popularity_filters()
    
    # Test API popularity endpoints
    test_api_popularity_filter()
    
    # Test genre assignments
    test_genre_assignments()
    
    # Test API genre filters
    test_genre_api_filter()
    
    print(f"\n🎉 Testing Complete!")
    print("=" * 30)
    
    print(f"\n💡 Summary:")
    print("  ✅ Popularity filters: Check distribution and API endpoints")
    print("  ✅ Genre assignments: Verify authenticity and accuracy")
    print("  ✅ API filters: Test genre and popularity filtering")
    print("  ✅ Recommendations: Ensure genre-specific results")
    
    print(f"\n🎯 Key Checks:")
    print("  • Popularity ranges are well distributed")
    print("  • Amapiano songs are from authentic South African artists")
    print("  • Genre-specific recommendations return correct genres")
    print("  • API endpoints respond correctly with filtered results")

if __name__ == "__main__":
    main()
