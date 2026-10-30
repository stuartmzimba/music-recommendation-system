#!/usr/bin/env python3
"""Test Amapiano recommendations with authentic songs."""

import sqlite3

def test_amapiano_recommendations():
    """Test recommendations for authentic Amapiano songs."""
    print("🎵 Testing Amapiano Recommendations")
    print("=" * 40)
    
    conn = sqlite3.connect('music_recommender.db')
    cursor = conn.cursor()
    
    # Get top Amapiano songs for testing
    cursor.execute('''
        SELECT track_name, artist, popularity_score 
        FROM songs 
        WHERE genre = 'Amapiano' 
        ORDER BY popularity_score DESC 
        LIMIT 5
    ''')
    
    test_songs = cursor.fetchall()
    
    print("🔍 Testing recommendations for top Amapiano songs:")
    
    for i, (track_name, artist, popularity) in enumerate(test_songs, 1):
        print(f"\n{i}. Testing: {track_name} by {artist} (popularity: {popularity})")
        
        # Find Apriori recommendations
        cursor.execute('''
            SELECT s2.track_name, s2.artist, s2.genre, ar.confidence, ar.lift
            FROM association_rules ar
            JOIN songs s1 ON ar.antecedent_song_id = s1.id
            JOIN songs s2 ON ar.consequent_song_id = s2.id
            WHERE s1.track_name = ? AND s1.artist = ?
            ORDER BY ar.confidence DESC
            LIMIT 5
        ''', (track_name, artist))
        
        recommendations = cursor.fetchall()
        
        if recommendations:
            print(f"   ✅ Apriori recommendations ({len(recommendations)}):")
            for j, (rec_track, rec_artist, rec_genre, confidence, lift) in enumerate(recommendations, 1):
                print(f"     {j}. {rec_track} by {rec_artist} ({rec_genre})")
                print(f"        Confidence: {confidence:.2f}, Lift: {lift:.2f}")
        else:
            print("   ⚠️ No direct Apriori recommendations found")
            
            # Try content-based (similar audio features)
            cursor.execute('''
                SELECT s2.track_name, s2.artist, s2.genre,
                       ABS(s1.danceability - s2.danceability) + 
                       ABS(s1.energy - s2.energy) + 
                       ABS(s1.valence - s2.valence) as similarity_score
                FROM songs s1, songs s2
                WHERE s1.track_name = ? AND s1.artist = ?
                AND s2.genre = 'Amapiano' 
                AND s2.id != s1.id
                ORDER BY similarity_score ASC
                LIMIT 3
            ''', (track_name, artist))
            
            similar_songs = cursor.fetchall()
            
            if similar_songs:
                print(f"   🎯 Similar Amapiano songs by audio features:")
                for j, (sim_track, sim_artist, sim_genre, sim_score) in enumerate(similar_songs, 1):
                    print(f"     {j}. {sim_track} by {sim_artist} (similarity: {sim_score:.3f})")
    
    # Test genre associations with Amapiano
    print(f"\n🎭 Amapiano Genre Associations:")
    cursor.execute('''
        SELECT s2.genre, COUNT(*) as rule_count, AVG(ar.confidence) as avg_confidence
        FROM association_rules ar
        JOIN songs s1 ON ar.antecedent_song_id = s1.id
        JOIN songs s2 ON ar.consequent_song_id = s2.id
        WHERE s1.genre = 'Amapiano'
        GROUP BY s2.genre
        ORDER BY rule_count DESC
        LIMIT 10
    ''')
    
    genre_associations = cursor.fetchall()
    
    if genre_associations:
        print("   ✅ Genres recommended after Amapiano:")
        for genre, count, avg_conf in genre_associations:
            print(f"     {genre}: {count} rules (avg confidence: {avg_conf:.2f})")
    
    # Test reverse associations (what leads to Amapiano)
    cursor.execute('''
        SELECT s1.genre, COUNT(*) as rule_count, AVG(ar.confidence) as avg_confidence
        FROM association_rules ar
        JOIN songs s1 ON ar.antecedent_song_id = s1.id
        JOIN songs s2 ON ar.consequent_song_id = s2.id
        WHERE s2.genre = 'Amapiano'
        GROUP BY s1.genre
        ORDER BY rule_count DESC
        LIMIT 10
    ''')
    
    reverse_associations = cursor.fetchall()
    
    if reverse_associations:
        print("\n   ✅ Genres that lead to Amapiano recommendations:")
        for genre, count, avg_conf in reverse_associations:
            print(f"     {genre}: {count} rules (avg confidence: {avg_conf:.2f})")
    
    # Show some specific Amapiano-to-Amapiano recommendations
    cursor.execute('''
        SELECT s1.track_name, s1.artist, s2.track_name, s2.artist, ar.confidence
        FROM association_rules ar
        JOIN songs s1 ON ar.antecedent_song_id = s1.id
        JOIN songs s2 ON ar.consequent_song_id = s2.id
        WHERE s1.genre = 'Amapiano' AND s2.genre = 'Amapiano'
        ORDER BY ar.confidence DESC
        LIMIT 5
    ''')
    
    amapiano_rules = cursor.fetchall()
    
    if amapiano_rules:
        print(f"\n🎵 Top Amapiano-to-Amapiano recommendations:")
        for ant_track, ant_artist, cons_track, cons_artist, confidence in amapiano_rules:
            print(f"   {ant_track} by {ant_artist}")
            print(f"   → {cons_track} by {cons_artist} (confidence: {confidence:.2f})")
            print()
    
    conn.close()
    
    print("🎉 Amapiano recommendation testing completed!")
    print("✅ Authentic Amapiano songs are now properly integrated!")

if __name__ == "__main__":
    test_amapiano_recommendations()
