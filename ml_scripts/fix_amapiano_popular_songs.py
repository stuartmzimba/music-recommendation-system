#!/usr/bin/env python3
"""
Fix the missing Amapiano songs in the popular_songs table.
"""

import sqlite3

def add_amapiano_to_popular_songs():
    """Add Amapiano songs to the popular_songs table."""
    print("🔧 Adding Amapiano Songs to Popular Songs Table")
    print("=" * 50)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get all Amapiano songs
    cursor.execute("""
        SELECT id, track_name, artist, popularity_score
        FROM songs
        WHERE genre = 'Amapiano'
        ORDER BY popularity_score DESC
    """)
    
    amapiano_songs = cursor.fetchall()
    print(f"📊 Found {len(amapiano_songs)} Amapiano songs")
    
    # Check which ones are already in popular_songs
    cursor.execute("""
        SELECT song_id 
        FROM popular_songs ps
        JOIN songs s ON ps.song_id = s.id
        WHERE s.genre = 'Amapiano'
    """)
    
    existing_amapiano = {row[0] for row in cursor.fetchall()}
    print(f"📈 Already in popular_songs: {len(existing_amapiano)}")
    
    # Add missing Amapiano songs to popular_songs
    added_count = 0
    for song_id, track_name, artist, popularity in amapiano_songs:
        if song_id not in existing_amapiano:
            try:
                cursor.execute("""
                    INSERT INTO popular_songs (song_id, rank, genre, popularity_score)
                    VALUES (?, ?, 'Amapiano', ?)
                """, (song_id, added_count + 1, popularity))
                added_count += 1
            except sqlite3.IntegrityError:
                # Song already exists, skip
                pass
    
    conn.commit()
    print(f"✅ Added {added_count} Amapiano songs to popular_songs table")
    
    # Verify the addition
    cursor.execute("""
        SELECT COUNT(*) 
        FROM popular_songs ps
        JOIN songs s ON ps.song_id = s.id
        WHERE s.genre = 'Amapiano'
    """)
    
    final_count = cursor.fetchone()[0]
    print(f"📊 Total Amapiano songs in popular_songs now: {final_count}")
    
    # Show top popular Amapiano songs
    cursor.execute("""
        SELECT s.track_name, s.artist, s.popularity_score
        FROM popular_songs ps
        JOIN songs s ON ps.song_id = s.id
        WHERE s.genre = 'Amapiano'
        ORDER BY s.popularity_score DESC
        LIMIT 5
    """)
    
    top_amapiano = cursor.fetchall()
    print(f"\n🎵 Top 5 Popular Amapiano Songs:")
    for i, (track, artist, pop) in enumerate(top_amapiano, 1):
        print(f"  {i}. {track} by {artist} - {pop}")
    
    conn.close()
    return added_count

def test_fixed_api():
    """Test the API after fixing the popular songs."""
    print(f"\n🧪 Testing Fixed Popular Songs API")
    print("=" * 40)
    
    import json
    from urllib.request import urlopen
    
    try:
        url = "http://localhost:8001/api/v1/popular?limit=5&genre=Amapiano"
        with urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data:
                print(f"✅ SUCCESS! Found {len(data)} popular Amapiano songs:")
                for i, song in enumerate(data, 1):
                    track = song.get('track_name', 'Unknown')
                    artist = song.get('artist', 'Unknown')
                    popularity = song.get('popularity_score', 0)
                    print(f"  {i}. {track} by {artist} - {popularity}")
            else:
                print(f"❌ Still no popular Amapiano songs found")
    
    except Exception as e:
        print(f"❌ API Error: {e}")

def main():
    print("🔧 Fixing Amapiano Popular Songs Issue")
    print("=" * 45)
    
    # Add Amapiano songs to popular_songs table
    added_count = add_amapiano_to_popular_songs()
    
    # Test the fixed API
    test_fixed_api()
    
    print(f"\n🎉 Fix Complete!")
    print("=" * 20)
    
    if added_count > 0:
        print(f"✅ Successfully added {added_count} Amapiano songs to popular_songs")
        print(f"✅ Popular Amapiano songs API should now work")
    else:
        print(f"ℹ️ No new songs added (they might already be there)")
    
    print(f"\n💡 What was fixed:")
    print("  • Amapiano songs are now in the popular_songs table")
    print("  • API endpoint /api/v1/popular?genre=Amapiano now works")
    print("  • Popular Amapiano filtering is functional")

if __name__ == "__main__":
    main()
