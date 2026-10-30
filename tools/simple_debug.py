#!/usr/bin/env python3
"""
Simple debug of why Apriori isn't working in the API.
"""

import sqlite3

def debug_song_search():
    """Debug the song search logic."""
    print("🔍 Debugging Song Search Logic")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Test the exact search logic from the service
    basket = ["Abantwana bakho"]
    
    for item in basket:
        print(f"\n🎵 Searching for: '{item}'")
        
        # Test track name search (ILIKE equivalent)
        cursor.execute("""
            SELECT id, track_name, artist 
            FROM songs 
            WHERE track_name LIKE ? COLLATE NOCASE
        """, (f"%{item}%",))
        
        track_matches = cursor.fetchall()
        print(f"  Track name matches: {len(track_matches)}")
        for song_id, track, artist in track_matches:
            print(f"    - {track} by {artist} (ID: {song_id})")
        
        # Test artist search (ILIKE equivalent)
        cursor.execute("""
            SELECT id, track_name, artist 
            FROM songs 
            WHERE artist LIKE ? COLLATE NOCASE
        """, (f"%{item}%",))
        
        artist_matches = cursor.fetchall()
        print(f"  Artist matches: {len(artist_matches)}")
        for song_id, track, artist in artist_matches:
            print(f"    - {track} by {artist} (ID: {song_id})")
        
        # Combined search (OR logic)
        cursor.execute("""
            SELECT id, track_name, artist 
            FROM songs 
            WHERE track_name LIKE ? COLLATE NOCASE 
               OR artist LIKE ? COLLATE NOCASE
        """, (f"%{item}%", f"%{item}%"))
        
        all_matches = cursor.fetchall()
        print(f"  Combined matches: {len(all_matches)}")
        
        if all_matches:
            print(f"  ✅ Songs found for '{item}'")
            
            # Check association rules for each match
            for song_id, track, artist in all_matches:
                cursor.execute("""
                    SELECT COUNT(*) FROM association_rules 
                    WHERE antecedent_song_id = ?
                """, (song_id,))
                
                rule_count = cursor.fetchone()[0]
                print(f"    {track}: {rule_count} association rules")
                
                if rule_count > 0:
                    # Show top 2 rules
                    cursor.execute("""
                        SELECT s.track_name, s.artist, ar.confidence
                        FROM association_rules ar
                        JOIN songs s ON ar.consequent_song_id = s.id
                        WHERE ar.antecedent_song_id = ?
                        ORDER BY ar.confidence DESC
                        LIMIT 2
                    """, (song_id,))
                    
                    rules = cursor.fetchall()
                    for rec_track, rec_artist, conf in rules:
                        print(f"      → {rec_track} by {rec_artist} (conf: {conf:.2f})")
        else:
            print(f"  ❌ No songs found for '{item}'")
    
    conn.close()

def test_exact_song_name():
    """Test with the exact song name from database."""
    print(f"\n🎯 Testing with Exact Song Name")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get the exact song name
    cursor.execute("""
        SELECT track_name, artist 
        FROM songs 
        WHERE track_name LIKE '%Abantwana%'
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        exact_track, exact_artist = result
        print(f"🎵 Exact song name: '{exact_track}'")
        print(f"🎤 Artist: '{exact_artist}'")
        
        # Test API search with exact name
        test_items = [
            exact_track,  # Full exact name
            "Abantwana Bakho",  # Partial name
            "abantwana bakho",  # Lowercase
            "Abantwana",  # Just first word
        ]
        
        for test_item in test_items:
            print(f"\n  Testing search: '{test_item}'")
            
            cursor.execute("""
                SELECT COUNT(*) FROM songs 
                WHERE track_name LIKE ? COLLATE NOCASE 
                   OR artist LIKE ? COLLATE NOCASE
            """, (f"%{test_item}%", f"%{test_item}%"))
            
            count = cursor.fetchone()[0]
            print(f"    Matches: {count}")
    
    conn.close()

def main():
    print("🔧 Simple Apriori Debug")
    print("=" * 30)
    
    debug_song_search()
    test_exact_song_name()
    
    print(f"\n💡 Key Insights:")
    print("  • If songs are found but have 0 rules → Database issue")
    print("  • If no songs are found → Search logic issue")
    print("  • If songs found with rules → API service issue")

if __name__ == "__main__":
    main()
