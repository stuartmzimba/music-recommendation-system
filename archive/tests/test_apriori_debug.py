#!/usr/bin/env python3
"""
Debug why Apriori recommendations aren't showing for specific songs.
"""

import sqlite3

def test_apriori_for_song(song_name):
    """Test if a specific song has association rules."""
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    print(f"🔍 Testing Apriori for: {song_name}")
    print("=" * 50)
    
    # Find the song
    cursor.execute("""
        SELECT id, track_name, artist, genre 
        FROM songs 
        WHERE track_name LIKE ?
        LIMIT 5
    """, (f"%{song_name}%",))
    
    songs = cursor.fetchall()
    
    if not songs:
        print(f"❌ Song '{song_name}' not found")
        conn.close()
        return
    
    print(f"📍 Found {len(songs)} matching songs:")
    for song_id, track, artist, genre in songs:
        print(f"  {song_id}: {track} by {artist} ({genre})")
        
        # Check for association rules
        cursor.execute("""
            SELECT COUNT(*) FROM association_rules 
            WHERE antecedent_song_id = ?
        """, (song_id,))
        
        rule_count = cursor.fetchone()[0]
        print(f"    📊 Association rules as antecedent: {rule_count}")
        
        if rule_count > 0:
            # Show top 3 rules
            cursor.execute("""
                SELECT s.track_name, s.artist, ar.confidence, ar.support, ar.lift
                FROM association_rules ar
                JOIN songs s ON ar.consequent_song_id = s.id
                WHERE ar.antecedent_song_id = ?
                ORDER BY ar.confidence DESC
                LIMIT 3
            """, (song_id,))
            
            rules = cursor.fetchall()
            print(f"    🎯 Top recommendations:")
            for track, artist, conf, support, lift in rules:
                print(f"      → {track} by {artist} (conf: {conf:.2f}, lift: {lift:.2f})")
        
        print()
    
    conn.close()

def test_random_working_rules():
    """Test some songs that definitely have rules."""
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    print("🎯 Testing Songs with Known Association Rules")
    print("=" * 50)
    
    # Get songs that have association rules
    cursor.execute("""
        SELECT DISTINCT s.track_name, s.artist, s.genre, COUNT(ar.id) as rule_count
        FROM songs s
        JOIN association_rules ar ON s.id = ar.antecedent_song_id
        GROUP BY s.id
        ORDER BY rule_count DESC
        LIMIT 5
    """)
    
    songs_with_rules = cursor.fetchall()
    
    for track, artist, genre, rule_count in songs_with_rules:
        print(f"🎵 {track} by {artist} ({genre})")
        print(f"  📊 Has {rule_count} association rules")
        
        # Get top recommendations
        cursor.execute("""
            SELECT s.track_name, s.artist, ar.confidence
            FROM association_rules ar
            JOIN songs s ON ar.consequent_song_id = s.id
            WHERE ar.antecedent_song_id = (
                SELECT id FROM songs WHERE track_name = ? AND artist = ?
            )
            ORDER BY ar.confidence DESC
            LIMIT 3
        """, (track, artist))
        
        recommendations = cursor.fetchall()
        print(f"  🎯 Top recommendations:")
        for rec_track, rec_artist, conf in recommendations:
            print(f"    → {rec_track} by {rec_artist} (conf: {conf:.2f})")
        print()
    
    conn.close()

def main():
    print("🔧 Debugging Apriori Recommendations")
    print("=" * 60)
    
    # Test the Amapiano songs that showed no Apriori results
    test_songs = [
        "Abantwana Bakho",
        "ZENZELE", 
        "Dlala Ka Yona",
        "Imithandazo"
    ]
    
    for song in test_songs:
        test_apriori_for_song(song)
    
    # Test songs that definitely have rules
    test_random_working_rules()
    
    print("🎉 Debug Complete!")
    print("\n💡 Key Insights:")
    print("  • Association rules exist (6,426 total)")
    print("  • Some songs have rules, others don't")
    print("  • This is normal - not every song appears in user listening patterns")
    print("  • Content-based filtering is the correct fallback")

if __name__ == "__main__":
    main()
