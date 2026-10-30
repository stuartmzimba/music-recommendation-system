#!/usr/bin/env python3
"""Test Apriori association rules."""

import sqlite3

def test_apriori_rules():
    """Test the generated association rules."""
    print("🔍 Testing Apriori Association Rules")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Count total rules
    cursor.execute('SELECT COUNT(*) FROM association_rules')
    total_rules = cursor.fetchone()[0]
    print(f"📊 Total association rules: {total_rules}")
    
    if total_rules == 0:
        print("❌ No association rules found!")
        conn.close()
        return
    
    # Get top rules by confidence
    cursor.execute('''
        SELECT ar.confidence, ar.support, ar.lift,
               s1.track_name as ant_song, s1.artist as ant_artist,
               s2.track_name as cons_song, s2.artist as cons_artist
        FROM association_rules ar
        JOIN songs s1 ON ar.antecedent_song_id = s1.id
        JOIN songs s2 ON ar.consequent_song_id = s2.id
        ORDER BY ar.confidence DESC
        LIMIT 10
    ''')
    
    top_rules = cursor.fetchall()
    
    print(f"\n🎵 Top 10 association rules by confidence:")
    for i, rule in enumerate(top_rules, 1):
        confidence, support, lift, ant_song, ant_artist, cons_song, cons_artist = rule
        print(f"  {i:2d}. {ant_song} by {ant_artist}")
        print(f"      → {cons_song} by {cons_artist}")
        print(f"      Confidence: {confidence:.2f}, Support: {support:.3f}, Lift: {lift:.2f}")
        print()
    
    # Test recommendation for a specific song
    print("🎯 Testing recommendation for a specific song...")
    cursor.execute('''
        SELECT s.track_name, s.artist, s.genre
        FROM songs s
        WHERE s.genre = 'Afrobeats'
        ORDER BY s.popularity_score DESC
        LIMIT 1
    ''')
    
    test_song = cursor.fetchone()
    if test_song:
        track_name, artist, genre = test_song
        print(f"Test song: {track_name} by {artist} ({genre})")
        
        # Find recommendations using association rules
        cursor.execute('''
            SELECT s2.track_name, s2.artist, s2.genre, ar.confidence
            FROM association_rules ar
            JOIN songs s1 ON ar.antecedent_song_id = s1.id
            JOIN songs s2 ON ar.consequent_song_id = s2.id
            WHERE s1.track_name = ? AND s1.artist = ?
            ORDER BY ar.confidence DESC
            LIMIT 5
        ''', (track_name, artist))
        
        recommendations = cursor.fetchall()
        
        if recommendations:
            print(f"\n🎵 Apriori recommendations for '{track_name}':")
            for i, rec in enumerate(recommendations, 1):
                rec_track, rec_artist, rec_genre, confidence = rec
                print(f"  {i}. {rec_track} by {rec_artist} ({rec_genre}) - Confidence: {confidence:.2f}")
        else:
            print(f"  ⚠️ No direct Apriori recommendations found for this song")
    
    # Test genre distribution in rules
    cursor.execute('''
        SELECT s1.genre as ant_genre, s2.genre as cons_genre, COUNT(*) as rule_count
        FROM association_rules ar
        JOIN songs s1 ON ar.antecedent_song_id = s1.id
        JOIN songs s2 ON ar.consequent_song_id = s2.id
        GROUP BY s1.genre, s2.genre
        ORDER BY rule_count DESC
        LIMIT 10
    ''')
    
    genre_rules = cursor.fetchall()
    
    print(f"\n🎭 Top genre associations:")
    for ant_genre, cons_genre, count in genre_rules:
        print(f"  {ant_genre} → {cons_genre}: {count} rules")
    
    conn.close()
    print("\n✅ Apriori testing completed!")

if __name__ == "__main__":
    test_apriori_rules()
